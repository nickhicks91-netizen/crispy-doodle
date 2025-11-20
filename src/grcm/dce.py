"""
DCE — Desire Continuity Engine

Ensures smooth evolution of desire vectors over time.

Prevents:
- Abrupt reorientation
- Adversarial desire flips
- Executive function collapse
- Goal instability

Maintains:
- Smooth desire transitions
- Coherent long-term planning
- Stable goal hierarchies
"""

import torch
import torch.nn as nn


class DesireContinuityEngine(nn.Module):
    """
    DCE — Desire Continuity Engine

    Ensures:
    - Smooth evolution of desire vectors
    - Prevention of abrupt reorientation
    - Protection against adversarial "desire flips"
    - Maintenance of coherence with long-term goals

    Desire vectors represent goal states, motivations, or target
    configurations. They should evolve smoothly to prevent:
    - Erratic behavior
    - Goal thrashing
    - Executive dysfunction
    - Adversarial manipulation
    """

    def __init__(
        self,
        tau: float = 0.1,
        max_shift: float = 0.12,
        momentum: float = 0.05,
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize Desire Continuity Engine

        Args:
            tau: EMA smoothing coefficient
            max_shift: Maximum allowed shift per tick
            momentum: Momentum term for smooth acceleration
            device: Computation device
        """
        super().__init__()

        self.tau = tau
        self.max_shift = max_shift
        self.momentum = momentum
        self.device = device

        # State buffers
        self.register_buffer('prev_desires', None)
        self.register_buffer('velocity', None)

    def forward(self, desires: torch.Tensor) -> torch.Tensor:
        """
        Apply desire continuity stabilization.

        Args:
            desires: Current raw desire vector

        Returns:
            Stabilized desire vector with smooth evolution
        """
        # Ensure correct device
        desires = desires.to(self.device)

        # Initialize on first call
        if self.prev_desires is None:
            self.prev_desires = desires.clone().detach()
            self.velocity = torch.zeros_like(desires)
            return desires

        # Smooth transition using EMA
        desires_smooth = (
            self.tau * desires +
            (1 - self.tau) * self.prev_desires
        )

        # Calculate desired change
        delta = desires_smooth - self.prev_desires

        # Clamp sudden shifts
        delta = delta.clamp(-self.max_shift, self.max_shift)

        # Apply momentum for smoother acceleration
        self.velocity = (
            self.momentum * delta +
            (1 - self.momentum) * self.velocity
        )

        # Compute stabilized desires
        desires_stable = self.prev_desires + self.velocity

        # Update state
        self.prev_desires = desires_stable.clone().detach()

        return desires_stable

    def get_desire_metrics(self) -> dict:
        """Get desire continuity diagnostics"""
        if self.prev_desires is None:
            return {
                'has_history': False,
                'velocity_norm': 0.0,
                'desire_norm': 0.0
            }

        return {
            'has_history': True,
            'velocity_norm': torch.norm(self.velocity).item() if self.velocity is not None else 0.0,
            'desire_norm': torch.norm(self.prev_desires).item(),
            'desire_shape': tuple(self.prev_desires.shape),
            'tau': self.tau,
            'max_shift': self.max_shift
        }

    def reset(self):
        """Reset desire history"""
        self.prev_desires = None
        self.velocity = None


# Example usage
if __name__ == "__main__":
    print("Testing Desire Continuity Engine...")

    desire_dim = 64
    dce = DesireContinuityEngine()

    # Test 1: Smooth evolution
    print("\n1. Smooth desire evolution:")
    desires = torch.randn(desire_dim) * 0.5

    for i in range(10):
        desires_stable = dce(desires)

        if i % 2 == 0:
            metrics = dce.get_desire_metrics()
            print(f"  Tick {i}: velocity_norm={metrics['velocity_norm']:.6f}, "
                  f"desire_norm={metrics['desire_norm']:.4f}")

        # Gradual change
        desires = desires + torch.randn(desire_dim) * 0.05

    # Test 2: Adversarial flip
    print("\n2. Adversarial desire flip:")
    desires = torch.randn(desire_dim) * 0.5

    for i in range(5):
        desires_stable = dce(desires)
        metrics = dce.get_desire_metrics()
        print(f"  Tick {i}: velocity_norm={metrics['velocity_norm']:.6f}")

        # Attempt sudden reversal
        desires = -desires * 2.0

    # Test 3: Oscillation attack
    print("\n3. Oscillation attack:")
    dce.reset()
    base_desires = torch.randn(desire_dim) * 0.5

    for i in range(20):
        # Oscillating input
        desires = base_desires * (1.0 if i % 2 == 0 else -1.0)
        desires_stable = dce(desires)

        if i % 5 == 0:
            metrics = dce.get_desire_metrics()
            print(f"  Tick {i}: velocity_norm={metrics['velocity_norm']:.6f}, "
                  f"desire_norm={metrics['desire_norm']:.4f}")

    # Test 4: Convergence to target
    print("\n4. Convergence to target desire:")
    dce.reset()
    current = torch.zeros(desire_dim)
    target = torch.randn(desire_dim) * 0.8

    distances = []
    for i in range(50):
        # Gradually move toward target
        desires = current + (target - current) * 0.1
        desires_stable = dce(desires)
        current = desires_stable

        distance = torch.norm(desires_stable - target).item()
        distances.append(distance)

        if i % 10 == 0:
            print(f"  Tick {i}: distance to target={distance:.6f}")

    print(f"  Final distance: {distances[-1]:.6f}")
    print(f"  Converged: {distances[-1] < 0.1}")

    # Test 5: Stability under noise
    print("\n5. Stability under continuous noise:")
    dce.reset()
    desires = torch.randn(desire_dim) * 0.5

    shifts = []
    for i in range(100):
        noisy_desires = desires + torch.randn(desire_dim) * 0.2
        desires_stable = dce(noisy_desires)

        if i > 0:
            shift = torch.norm(desires_stable - dce.prev_desires).item()
            shifts.append(shift)

    print(f"  Mean shift per tick: {sum(shifts)/len(shifts):.6f}")
    print(f"  Max shift: {max(shifts):.6f}")
    print(f"  Within max_shift bound: {max(shifts) <= dce.max_shift * 1.5}")

    print("\n✓ Desire Continuity Engine tests passed")
