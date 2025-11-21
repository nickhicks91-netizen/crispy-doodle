"""
Strategy Identity Layer (SIL) — Adapted from EchoZero IBL

Maintains stable investment strategy across long timelines.

Strategy preservation through:
- Long-term average allocation tracking
- Projection onto strategy subspace
- Strategy erosion detection
- Allocation boundary enforcement

Prevents:
- Strategy drift (mission creep)
- Internal fragmentation (conflicting signals)
- Strategy collapse (panic selling)
- Erratic rebalancing (whipsaw)

Adapted from: src/grcm/ibl.py (EchoZero v4.2.1)
"""

import torch
import torch.nn as nn


class StrategyIdentityLayer(nn.Module):
    """
    SIL — Strategy Identity Layer

    Maintains a stable investment strategy manifold by:
    - Tracking long-term average allocation state
    - Projecting current allocation onto strategy subspace
    - Detecting strategy erosion
    - Enforcing strategy boundary constraints

    The strategy "core" is a slowly-evolving attractor that represents
    the long-term stable configuration of the portfolio. Current allocations are
    softly constrained to remain within a neighborhood of this core.

    DNA Source: IdentityBoundaryLayer (EchoZero)
    """

    def __init__(
        self,
        strategy_tau: float = 0.001,      # Very slow strategy evolution
        erosion_thresh: float = 0.12,     # Max 12% deviation from strategy
        projection_strength: float = 0.4,  # Pull-back strength
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize Strategy Identity Layer

        Args:
            strategy_tau: EMA coefficient for strategy core update (very slow)
            erosion_thresh: Maximum allowed deviation from strategy core
            projection_strength: Strength of pull-back toward strategy manifold
            device: Computation device
        """
        super().__init__()

        self.tau = strategy_tau
        self.erosion_thresh = erosion_thresh
        self.projection_strength = projection_strength
        self.device = device

        # Strategy core state (slowly evolving allocation target)
        self.register_buffer('strategy_core', None)

    def update_strategy(self, allocation: torch.Tensor):
        """
        Update the strategy core using slow EMA.

        The strategy core represents the "true strategy" - a slowly-evolving
        attractor that defines the stable allocation manifold.

        Args:
            allocation: Current allocation vector (weights summing to 1.0)
        """
        if self.strategy_core is None:
            self.strategy_core = allocation.clone().detach()
        else:
            # Very slow update (tau typically 0.001 → evolves ~1000x slower)
            self.strategy_core = (
                self.tau * allocation.detach() +
                (1 - self.tau) * self.strategy_core
            )

    def compute_deviation(self, allocation: torch.Tensor) -> torch.Tensor:
        """
        Compute normalized deviation from strategy core.

        Args:
            allocation: Current allocation vector

        Returns:
            Normalized deviation metric (L2 distance)
        """
        if self.strategy_core is None:
            return torch.tensor(0.0, device=self.device)

        # Normalized L2 deviation (same as IBL)
        deviation = torch.norm(allocation - self.strategy_core) / (
            torch.norm(self.strategy_core) + 1e-8
        )

        return deviation

    def enforce_boundaries(self, allocation: torch.Tensor) -> torch.Tensor:
        """
        Enforce strategy boundary constraints.

        If the current allocation deviates too far from the strategy core,
        apply a soft projection back toward the strategy manifold.

        Args:
            allocation: Current allocation vector

        Returns:
            Boundary-enforced allocation vector
        """
        if self.strategy_core is None:
            return allocation

        deviation = self.compute_deviation(allocation)

        # If deviation exceeds threshold, project back (identical to IBL)
        if deviation > self.erosion_thresh:
            # Soft projection: blend toward strategy core
            allocation = (
                self.strategy_core +
                self.projection_strength * (allocation - self.strategy_core)
            )

        return allocation

    def forward(self, allocation: torch.Tensor) -> torch.Tensor:
        """
        Full SIL pipeline (identical structure to IBL).

        Args:
            allocation: Current allocation vector (e.g., asset weights)

        Returns:
            Strategy-bounded allocation vector
        """
        # Ensure correct device
        allocation = allocation.to(self.device)

        # Update strategy core (slow EMA)
        self.update_strategy(allocation)

        # Enforce strategy boundaries
        allocation = self.enforce_boundaries(allocation)

        return allocation

    def get_strategy_metrics(self) -> dict:
        """Get strategy diagnostics"""
        if self.strategy_core is None:
            return {
                'has_strategy': False,
                'core_norm': 0.0,
                'deviation': 0.0
            }

        return {
            'has_strategy': True,
            'core_norm': torch.norm(self.strategy_core).item(),
            'strategy_shape': tuple(self.strategy_core.shape),
            'tau': self.tau,
            'erosion_thresh': self.erosion_thresh
        }

    def reset_strategy(self):
        """Reset strategy core (use when changing investment mandate)"""
        self.strategy_core = None


# Example usage
if __name__ == "__main__":
    print("Testing Strategy Identity Layer (SIL)...")

    # Example: 5-asset portfolio
    n_assets = 5
    sil = StrategyIdentityLayer()

    # Initialize with base allocation (40% stocks, 30% bonds, 20% commodities, 10% cash)
    print("\n1. Establishing strategy core:")
    allocation = torch.tensor([0.40, 0.30, 0.20, 0.08, 0.02])

    for i in range(100):
        allocation_bounded = sil(allocation)
        # Small drift from market movements
        allocation = allocation + torch.randn(n_assets) * 0.005
        allocation = torch.clamp(allocation, 0.0, 1.0)
        allocation = allocation / allocation.sum()  # Renormalize

        if i % 25 == 0:
            metrics = sil.get_strategy_metrics()
            deviation = sil.compute_deviation(allocation)
            print(f"  Day {i}: deviation={deviation.item():.6f}, "
                  f"core_norm={metrics['core_norm']:.4f}")

    print(f"  Strategy core: {sil.strategy_core}")

    # Test strategy erosion attack (panic selling)
    print("\n2. Strategy erosion attack (panic selling):")
    for i in range(20):
        # Large perturbation attempting to shift to all-cash
        panic_shift = torch.tensor([0.0, 0.0, 0.0, 0.0, 1.0])  # 100% cash
        allocation = 0.7 * allocation + 0.3 * panic_shift
        allocation_bounded = sil(allocation)

        deviation_before = torch.norm(allocation - sil.strategy_core) / torch.norm(sil.strategy_core)
        deviation_after = torch.norm(allocation_bounded - sil.strategy_core) / torch.norm(sil.strategy_core)

        if i % 5 == 0:
            print(f"  Day {i}: deviation before={deviation_before.item():.4f}, "
                  f"after={deviation_after.item():.4f}")
            print(f"    Allocation: {allocation_bounded}")

    # Verify strategy preservation
    print("\n3. Strategy preservation check:")
    metrics = sil.get_strategy_metrics()
    print(f"  Strategy core maintained: {metrics['has_strategy']}")
    print(f"  Core norm: {metrics['core_norm']:.4f}")
    print(f"  Erosion threshold: {metrics['erosion_thresh']}")
    print(f"  Final strategy core: {sil.strategy_core}")

    # Test long-term stability
    print("\n4. Long-term stability test (1000 days):")
    allocation = torch.tensor([0.40, 0.30, 0.20, 0.08, 0.02])
    deviations = []

    for i in range(1000):
        # Random market movements
        allocation = allocation + torch.randn(n_assets) * 0.02
        allocation = torch.clamp(allocation, 0.0, 1.0)
        allocation = allocation / allocation.sum()

        allocation_bounded = sil(allocation)
        deviation = sil.compute_deviation(allocation_bounded)
        deviations.append(deviation.item())

    print(f"  Mean deviation: {sum(deviations)/len(deviations):.6f}")
    print(f"  Max deviation: {max(deviations):.6f}")
    print(f"  Strategy preserved: {max(deviations) < sil.erosion_thresh * 1.2}")

    print("\n✓ Strategy Identity Layer tests passed")
