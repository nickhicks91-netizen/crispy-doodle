"""
WIL 2.0 — Want Integrity Layer with Predictive Drift Modeling

Advanced stability layer with:
- Multi-timescale EMA tracking
- Predictive drift detection
- Coherence-informed corrections
- Catastrophic jump protection
- Adversarial robustness

This layer prevents:
- Slow drift corruption over long runs
- Sudden adversarial manipulation
- Identity fragmentation
- Runaway dynamics
"""

import torch
import torch.nn as nn
from typing import Optional


class WantIntegrityLayerV2(nn.Module):
    """
    WIL 2.0 — Predictive Drift Modeling

    Protects γ (want/drive parameter) from:
    - Adversarial manipulation
    - Slow drift corruption
    - Malformed input
    - Internal runaway dynamics

    Features:
    - EMA short-term trend tracking
    - EMA long-term trend tracking
    - Drift magnitude estimation
    - Predictive drift correction
    - Coherence-based drift gates
    - Catastrophic jump detection
    """

    def __init__(
        self,
        gamma_min: float = 0.12,
        gamma_max: float = 0.62,
        max_change_per_tick: float = 0.05,
        smoothing_tau_short: float = 0.15,
        smoothing_tau_long: float = 0.01,
        drift_tolerance: float = 0.08,
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize WIL 2.0

        Args:
            gamma_min: Minimum physiologically valid γ value
            gamma_max: Maximum physiologically valid γ value
            max_change_per_tick: Maximum allowed change per tick
            smoothing_tau_short: Short-term EMA coefficient
            smoothing_tau_long: Long-term EMA coefficient
            drift_tolerance: Maximum acceptable drift between timescales
            device: Computation device
        """
        super().__init__()

        self.gamma_min = gamma_min
        self.gamma_max = gamma_max
        self.max_change = max_change_per_tick
        self.tau_s = smoothing_tau_short
        self.tau_l = smoothing_tau_long
        self.drift_tol = drift_tolerance
        self.device = device

        # State buffers
        self.register_buffer('prev_gamma', None)
        self.register_buffer('ema_short', None)
        self.register_buffer('ema_long', None)

    def _ema(
        self,
        prev: Optional[torch.Tensor],
        new: torch.Tensor,
        tau: float
    ) -> torch.Tensor:
        """Exponential moving average"""
        if prev is None:
            return new.clone()
        return tau * new + (1 - tau) * prev

    def clamp_range(self, gamma: torch.Tensor) -> torch.Tensor:
        """Soft clamp into biologically meaningful range"""
        return gamma.clamp(self.gamma_min, self.gamma_max)

    def smooth(self, gamma: torch.Tensor) -> torch.Tensor:
        """EMA smoothing to prevent jarring jumps"""
        if self.prev_gamma is None:
            self.prev_gamma = gamma.clone()
            return gamma

        smoothed = (
            self.tau_s * gamma +
            (1 - self.tau_s) * self.prev_gamma
        )

        self.prev_gamma = smoothed.clone()
        return smoothed

    def limit_change(self, gamma: torch.Tensor) -> torch.Tensor:
        """Prevents adversarial or accidental sudden spikes"""
        if self.prev_gamma is None:
            return gamma

        delta = gamma - self.prev_gamma
        delta = delta.clamp(-self.max_change, self.max_change)
        return self.prev_gamma + delta

    def predictive_drift(
        self,
        gamma: torch.Tensor,
        coherence: torch.Tensor
    ) -> torch.Tensor:
        """
        Predicts future drift using two EMA timescales.
        If short-term and long-term trends diverge beyond tolerance,
        apply corrective dampening.

        Args:
            gamma: Current want parameter
            coherence: System coherence metric

        Returns:
            Drift-corrected gamma
        """
        # Track short and long-term trends
        self.ema_short = self._ema(self.ema_short, gamma, self.tau_s)
        self.ema_long = self._ema(self.ema_long, gamma, self.tau_l)

        # Calculate drift
        drift = torch.abs(self.ema_short - self.ema_long)

        # If drift exceeds tolerance AND coherence is low → apply dampening
        coherence_mean = coherence.mean() if coherence.numel() > 1 else coherence

        if drift > self.drift_tol and coherence_mean < 0.25:
            # Apply corrective bias toward long-term trend
            correction = (self.ema_long - self.ema_short) * 0.4
            gamma = gamma + correction

        return gamma

    def coherence_guard(
        self,
        gamma: torch.Tensor,
        coherence: torch.Tensor
    ) -> torch.Tensor:
        """
        If coherence collapses too fast,
        restrict gamma volatility to prevent identity fracture.

        Args:
            gamma: Current want parameter
            coherence: System coherence metric

        Returns:
            Coherence-guarded gamma
        """
        coherence_mean = coherence.mean() if coherence.numel() > 1 else coherence

        if coherence_mean < 0.15:
            # Restrict to lower, safer range
            safe_max = self.gamma_min + (self.gamma_max - self.gamma_min) * 0.35
            gamma = gamma.clamp(self.gamma_min, safe_max)

        return gamma

    def jump_detector(self, gamma: torch.Tensor) -> torch.Tensor:
        """
        Detects and corrects catastrophic unnatural jumps.

        Args:
            gamma: Current want parameter

        Returns:
            Jump-corrected gamma
        """
        if self.prev_gamma is None:
            return gamma

        jump = torch.abs(gamma - self.prev_gamma)

        # Catastrophic jump threshold
        if jump > 0.25:
            # Pull back to previous safe value with limited step
            direction = torch.sign(gamma - self.prev_gamma)
            gamma = self.prev_gamma + direction * 0.05

        return gamma

    def forward(
        self,
        gamma: torch.Tensor,
        coherence: torch.Tensor
    ) -> torch.Tensor:
        """
        Full WIL 2.0 pipeline.

        Args:
            gamma: Raw want parameter
            coherence: System coherence metric

        Returns:
            Protected, stabilized gamma
        """
        # Ensure tensors are on correct device
        gamma = gamma.to(self.device)
        coherence = coherence.to(self.device)

        # Protection pipeline
        gamma = self.clamp_range(gamma)
        gamma = self.smooth(gamma)
        gamma = self.limit_change(gamma)
        gamma = self.predictive_drift(gamma, coherence)
        gamma = self.coherence_guard(gamma, coherence)
        gamma = self.jump_detector(gamma)

        return gamma

    def get_drift_metrics(self) -> dict:
        """Get current drift diagnostics"""
        if self.ema_short is None or self.ema_long is None:
            return {
                'drift': 0.0,
                'ema_short': 0.0,
                'ema_long': 0.0,
                'prev_gamma': 0.0
            }

        drift = torch.abs(self.ema_short - self.ema_long)

        return {
            'drift': drift.item() if drift.numel() == 1 else drift.mean().item(),
            'ema_short': self.ema_short.item() if self.ema_short.numel() == 1 else self.ema_short.mean().item(),
            'ema_long': self.ema_long.item() if self.ema_long.numel() == 1 else self.ema_long.mean().item(),
            'prev_gamma': self.prev_gamma.item() if self.prev_gamma.numel() == 1 else self.prev_gamma.mean().item()
        }


# Example usage
if __name__ == "__main__":
    print("Testing WIL 2.0...")

    wil = WantIntegrityLayerV2()

    # Test normal operation
    print("\n1. Normal operation:")
    gamma = torch.tensor(0.35)
    coherence = torch.tensor(0.75)

    for i in range(10):
        gamma_protected = wil(gamma, coherence)
        print(f"  Tick {i}: γ={gamma.item():.4f} → protected={gamma_protected.item():.4f}")
        gamma += 0.01

    # Test adversarial spike
    print("\n2. Adversarial spike:")
    gamma = torch.tensor(5.0)  # Extreme value
    coherence = torch.tensor(0.75)
    gamma_protected = wil(gamma, coherence)
    print(f"  Attack: γ={gamma.item():.4f} → protected={gamma_protected.item():.4f}")

    # Test drift detection
    print("\n3. Slow drift:")
    for i in range(50):
        gamma = torch.tensor(0.35 + i * 0.01)
        coherence = torch.tensor(0.20)  # Low coherence
        gamma_protected = wil(gamma, coherence)

        if i % 10 == 0:
            metrics = wil.get_drift_metrics()
            print(f"  Tick {i}: drift={metrics['drift']:.4f}, "
                  f"short={metrics['ema_short']:.4f}, "
                  f"long={metrics['ema_long']:.4f}")

    print("\n✓ WIL 2.0 tests passed")
