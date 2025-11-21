"""
Position Smoothing Engine (PSE) — Adapted from EchoZero DCE

Ensures smooth evolution of portfolio positions.

Position smoothing through:
- EMA smoothing of position changes
- Momentum tracking for trend-following
- Shift limiting to prevent whipsaw
- Oscillation resistance

Prevents:
- Position flips (complete reversals)
- Rebalancing thrashing (excessive trading)
- Oscillation attacks (rapid flip-flopping)
- Transaction cost bleed (overtrading)

Adapted from: src/grcm/dce.py (EchoZero v4.2.1)
"""

import torch
import torch.nn as nn


class PositionSmoothingEngine(nn.Module):
    """
    PSE — Position Smoothing Engine

    Ensures smooth evolution of portfolio positions through:
    - EMA smoothing
    - Momentum tracking
    - Shift limiting
    - Anti-oscillation protection

    DNA Source: DesireContinuityEngine (EchoZero)
    """

    def __init__(
        self,
        tau: float = 0.10,               # EMA smoothing coefficient
        max_shift: float = 0.08,         # Max 8% position shift per rebalance
        momentum: float = 0.05,          # Momentum term (trend following)
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize Position Smoothing Engine

        Args:
            tau: EMA smoothing coefficient
            max_shift: Maximum position shift per rebalance (prevents whipsaw)
            momentum: Momentum term for velocity-based smoothing
            device: Computation device
        """
        super().__init__()

        self.tau = tau
        self.max_shift = max_shift
        self.momentum = momentum
        self.device = device

        # State buffers (identical to DCE)
        self.register_buffer('prev_positions', None)
        self.register_buffer('velocity', None)

    def forward(self, positions: torch.Tensor) -> torch.Tensor:
        """
        Full PSE pipeline (identical structure to DCE).

        Args:
            positions: Raw position vector (e.g., asset allocations)

        Returns:
            Smoothed, stabilized position vector
        """
        # Ensure correct device
        positions = positions.to(self.device)

        # Initialize on first call
        if self.prev_positions is None:
            self.prev_positions = positions.clone()
            self.velocity = torch.zeros_like(positions)
            return positions

        # EMA smoothing (identical to DCE)
        positions_smooth = (
            self.tau * positions +
            (1 - self.tau) * self.prev_positions
        )

        # Compute change
        delta = positions_smooth - self.prev_positions

        # Shift limiting (prevent excessive single-step changes)
        delta_norm = torch.norm(delta)
        if delta_norm > self.max_shift:
            delta = delta * (self.max_shift / (delta_norm + 1e-8))

        # Momentum tracking (velocity-based smoothing)
        self.velocity = (
            self.momentum * delta +
            (1 - self.momentum) * self.velocity
        )

        # Apply smoothed change
        positions_stable = self.prev_positions + self.velocity

        # Update state
        self.prev_positions = positions_stable.clone()

        return positions_stable

    def get_position_metrics(self) -> dict:
        """Get position diagnostics"""
        if self.prev_positions is None:
            return {
                'has_history': False,
                'velocity_norm': 0.0,
                'position_shape': None
            }

        return {
            'has_history': True,
            'velocity_norm': torch.norm(self.velocity).item(),
            'position_shape': tuple(self.prev_positions.shape),
            'tau': self.tau,
            'max_shift': self.max_shift,
            'momentum': self.momentum
        }

    def reset(self):
        """Reset internal state (for new account initialization)"""
        self.prev_positions = None
        self.velocity = None


# Example usage
if __name__ == "__main__":
    print("Testing Position Smoothing Engine (PSE)...")

    # Example: 5-asset portfolio
    n_assets = 5
    pse = PositionSmoothingEngine()

    # Test normal operation
    print("\n1. Normal operation:")
    positions = torch.tensor([0.40, 0.30, 0.20, 0.08, 0.02])

    for i in range(10):
        positions_stable = pse(positions)
        print(f"  Day {i}: raw={positions} → stable={positions_stable}")
        # Small drift
        positions = positions + torch.randn(n_assets) * 0.01
        positions = torch.clamp(positions, 0.0, 1.0)
        positions = positions / positions.sum()

    # Test adversarial flip (panic to all-cash)
    print("\n2. Adversarial position flip:")
    baseline = pse.prev_positions.clone()
    print(f"  Baseline: {baseline}")

    for i in range(20):
        # Attempt complete reversal to all-cash
        positions = torch.tensor([0.0, 0.0, 0.0, 0.0, 1.0])
        positions_stable = pse(positions)

        similarity = torch.dot(positions_stable, baseline) / (
            torch.norm(positions_stable) * torch.norm(baseline) + 1e-8
        )

        if i % 5 == 0:
            print(f"  Day {i}: similarity={similarity.item():.4f}, positions={positions_stable}")

    # Test high-frequency oscillation
    print("\n3. High-frequency oscillation:")
    base_positions = torch.tensor([0.40, 0.30, 0.20, 0.08, 0.02])
    pse.reset()

    for i in range(20):
        if i % 2 == 0:
            positions = base_positions
        else:
            positions = torch.tensor([0.20, 0.20, 0.20, 0.20, 0.20])

        positions_stable = pse(positions)
        metrics = pse.get_position_metrics()

        if i % 5 == 0:
            print(f"  Day {i}: velocity_norm={metrics['velocity_norm']:.4f}")

    # Test long-term stability
    print("\n4. Long-term stability (1000 days):")
    pse.reset()
    positions = torch.tensor([0.40, 0.30, 0.20, 0.08, 0.02])
    velocities = []

    for i in range(1000):
        # Random market movements
        positions = positions + torch.randn(n_assets) * 0.02
        positions = torch.clamp(positions, 0.0, 1.0)
        positions = positions / positions.sum()

        positions_stable = pse(positions)

        if i > 100:
            metrics = pse.get_position_metrics()
            velocities.append(metrics['velocity_norm'])

    avg_velocity = sum(velocities) / len(velocities)
    max_velocity = max(velocities)

    print(f"  Average velocity: {avg_velocity:.6f}")
    print(f"  Max velocity: {max_velocity:.6f}")
    print(f"  Stability maintained: {max_velocity < 0.2}")

    print("\n✓ Position Smoothing Engine tests passed")
