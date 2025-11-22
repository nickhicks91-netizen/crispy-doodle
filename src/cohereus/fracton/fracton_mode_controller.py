"""
Fracton Mode Controller — Master Constrained Mobility Controller

Orchestrates all Fracton Mode components:
- Charge map computation
- Mobility constraints
- Cluster decoupling
- Migration tensor
- Global stability projection

Creates geometry where harmful collective moves are mathematically restricted.

DNA Source: Constrained excitation physics → economic mobility geometry
"""

from .fracton_charge_map import FractonChargeMap
from .mobility_constraint import MobilityConstraint
from .cluster_constraint import ClusterConstraint
from .migration_tensor import MigrationTensor
from .stability_kernel import StabilityKernel


class FractonModeController:
    """
    Master controller for Fracton Mode v1.0.

    Executes complete pipeline:
    1. Compute fracton charge (mobility cost)
    2. Apply mobility constraints (limit individual movement)
    3. Decouple clusters (prevent synchronization)
    4. Apply migration tensor (allow multi-body, block single-body)
    5. Apply global stability projection

    Usage:
        fracton = FractonModeController()
        state = {"theta": ..., "phi": ..., "r": ...}
        stable_state = fracton.step(state)
    """

    def __init__(
        self,
        max_move: float = 0.02,
        coherence_threshold: float = 0.25,
        noise_strength: float = 0.01,
        migration_window: int = 7,
        lambda_param: float = 0.05
    ):
        """
        Initialize Fracton Mode controller.

        Args:
            max_move: Maximum individual mobility per cycle
            coherence_threshold: Max correlation before desync
            noise_strength: Decorrelation noise strength
            migration_window: Neighborhood window for consensus
            lambda_param: Global stability attraction strength
        """
        self.charge_map = FractonChargeMap()
        self.mobility = MobilityConstraint(max_move=max_move)
        self.cluster = ClusterConstraint(
            coherence_threshold=coherence_threshold,
            noise_strength=noise_strength
        )
        self.migrate = MigrationTensor(window=migration_window)
        self.kernel = StabilityKernel(lambda_param=lambda_param)

    def step(self, state: dict) -> dict:
        """
        Execute one Fracton Mode stabilization step.

        Args:
            state: State dict with 'theta', 'phi', 'r' arrays

        Returns:
            Fracton-stabilized state
        """
        # 1. Compute fracton charge (mobility cost based on local stress)
        charge = self.charge_map.compute_charge(state)

        # 2. Apply mobility constraints (limit individual movement)
        restricted = self.mobility.restrict(state, charge)

        # 3. Decouple clusters (prevent synchronization)
        decoupled = self.cluster.decouple(restricted)

        # 4. Apply migration tensor (multi-body consensus, resist single-body)
        migrated = self.migrate.migrate(decoupled, charge)

        # 5. Apply global stability projection
        final = self.kernel.project(migrated)

        return final


# Example usage
if __name__ == "__main__":
    import numpy as np

    print("Testing Fracton Mode Controller...")

    fracton = FractonModeController()

    # Test with unstable synchronized state
    print("\n1. Synchronized unstable state:")
    n = 100
    t = np.linspace(0, 1, n)

    # Highly correlated (synchronized)
    state = {
        "theta": t * 2,
        "phi": t,
        "r": t,  # Perfect correlation
    }

    # Measure synchronization
    orig_corr = np.corrcoef(state["theta"], state["r"])[0, 1]
    orig_var = np.var(state["theta"])

    stable = fracton.step(state)

    final_corr = np.corrcoef(stable["theta"], stable["r"])[0, 1]
    final_var = np.var(stable["theta"])

    print(f"  Original correlation: {orig_corr:.6f}")
    print(f"  Final correlation: {final_corr:.6f}")
    print(f"  Original variance: {orig_var:.6f}")
    print(f"  Final variance: {final_var:.6f}")
    print(f"  Desynchronization achieved: {orig_corr - final_corr > 0.1}")

    # Test with already-stable diverse state
    print("\n2. Already stable diverse state:")
    state_stable = {
        "theta": np.random.randn(n) * 0.1 + 0.5,
        "phi": np.random.randn(n) * 0.1 + 0.3,
        "r": 0.5 + np.random.rand(n) * 0.1,
    }

    stable_output = fracton.step(state_stable)

    change = np.mean(np.abs(stable_output["theta"] - state_stable["theta"]))
    print(f"  Mean change: {change:.6f}")
    print(f"  (Should be small - minimal intervention)")

    # Test multi-cycle convergence
    print("\n3. Multi-cycle convergence:")
    state = {
        "theta": np.random.randn(n),
        "phi": np.random.randn(n),
        "r": 0.5 + np.random.rand(n),
    }

    variances = []
    correlations = []

    for i in range(20):
        state = fracton.step(state)
        variances.append(np.var(state["theta"]))
        correlations.append(np.corrcoef(state["theta"], state["r"])[0, 1])

    print(f"  Initial variance: {variances[0]:.6f}")
    print(f"  Final variance: {variances[-1]:.6f}")
    print(f"  Final correlation: {abs(correlations[-1]):.6f}")
    print(f"  Converged to stable state: {variances[-1] < variances[0]}")

    print("\n✓ Fracton Mode Controller operational")
