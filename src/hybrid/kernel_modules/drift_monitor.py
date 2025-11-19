"""
Drift Monitor (v4.2.1)
-----------------------
Tracks ψ-drift and triggers corrections when drift exceeds thresholds.

Monitors:
- ψ-state drift magnitude
- Drift velocity (rate of change)
- Drift acceleration
- Coherence correlation with drift

Fixes from v4.2.0:
- Proper state management
- Batching support
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class DriftMonitor(nn.Module):
    """
    ψ-drift monitoring and analysis.
    """

    def __init__(
        self,
        drift_threshold: float = 0.5,
        velocity_threshold: float = 0.1,
        device: Optional[str] = None
    ):
        """
        Args:
            drift_threshold: Maximum acceptable drift magnitude
            velocity_threshold: Maximum acceptable drift velocity
            device: Device to place on
        """
        super().__init__()

        self.drift_threshold = drift_threshold
        self.velocity_threshold = velocity_threshold

        # Historical state tracking (buffers)
        self.register_buffer('prev_psi', None)
        self.register_buffer('prev_drift', torch.tensor(0.0))
        self.register_buffer('drift_history', torch.zeros(10))  # Last 10 drifts
        self.register_buffer('history_idx', torch.tensor(0))

        if device:
            self.to(device)

    def compute_drift(
        self,
        psi_current: torch.Tensor,
        psi_prev: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute drift magnitude.

        Args:
            psi_current: Current ψ state
            psi_prev: Previous ψ state (uses stored if None)

        Returns:
            drift: Drift magnitude
        """
        if psi_prev is None:
            if self.prev_psi is None:
                return torch.tensor(0.0)
            psi_prev = self.prev_psi

        # Compute L2 drift
        diff = psi_current - psi_prev
        drift = torch.mean(torch.abs(diff))

        return drift

    def compute_velocity(self, current_drift: torch.Tensor) -> torch.Tensor:
        """
        Compute drift velocity (change in drift).

        Args:
            current_drift: Current drift magnitude

        Returns:
            velocity: Drift velocity
        """
        velocity = current_drift - self.prev_drift
        return velocity

    def compute_acceleration(self) -> torch.Tensor:
        """
        Compute drift acceleration from history.

        Returns:
            acceleration: Drift acceleration
        """
        if self.history_idx < 2:
            return torch.tensor(0.0)

        # Get last 3 drift values
        recent = self.drift_history[max(0, self.history_idx - 3):self.history_idx]

        if len(recent) < 2:
            return torch.tensor(0.0)

        # Compute second derivative
        velocities = recent[1:] - recent[:-1]
        if len(velocities) < 2:
            return torch.tensor(0.0)

        acceleration = velocities[-1] - velocities[-2]
        return acceleration

    def update_history(self, drift: torch.Tensor):
        """
        Update drift history.

        Args:
            drift: Current drift value
        """
        idx = int(self.history_idx % 10)
        self.drift_history[idx] = drift
        self.history_idx += 1

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Monitor drift and generate alerts.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with drift, velocity, acceleration, drift_alert
        """
        psi = hybrid_out['psi']

        # Compute drift
        drift = self.compute_drift(psi)

        # Compute velocity
        velocity = self.compute_velocity(drift)

        # Compute acceleration
        acceleration = self.compute_acceleration()

        # Update history
        self.update_history(drift)

        # Check thresholds
        drift_alert = (drift > self.drift_threshold) or (torch.abs(velocity) > self.velocity_threshold)

        # Store current state
        with torch.no_grad():
            if self.prev_psi is None:
                self.register_buffer('prev_psi', psi.clone())
            else:
                self.prev_psi.copy_(psi)
            self.prev_drift = drift.clone()

        return {
            'drift': drift,
            'drift_velocity': velocity,
            'drift_acceleration': acceleration,
            'drift_alert': drift_alert
        }
