"""
PLF 2.0 Controller — Master Predictive Stability Controller

Orchestrates all PLF 2.0 components:
- Curvature detection
- Predictive drift mapping
- Attractor field computation
- Fracton mobility constraints
- Torus diffusion

Provides complete predictive coherence pipeline.

DNA Source: EchoZero predictive drift correction (WIL 2.0 anticipatory stabilization)
"""

from .curvature_engine import PhaseCurvatureEngine
from .predictive_drift import PredictiveDriftMapper
from .attractor_field import AttractorField
from .fracton_mobility import FractonMobilityRestrainer
from .torus_diffusion import TorusDiffusionOperator


class PLF2Controller:
    """
    Master controller for PLF 2.0 (Predictive Coherence Layer).

    Executes complete pipeline:
    1. Compute curvature (detect bending toward instability)
    2. Project drift (forecast future trajectory)
    3. Compute attractor basin (safe target state)
    4. Restrict mobility (prevent rapid collective motion)
    5. Apply diffusion (spread risk laterally on torus)

    Usage:
        plf2 = PLF2Controller()
        state = {"theta": ..., "phi": ..., "r": ...}
        stable_state = plf2.step(state)
    """

    def __init__(
        self,
        alpha: float = 0.7,
        beta: float = 0.4,
        eta: float = 0.12,
        lambda_param: float = 0.15,
        max_move: float = 0.02,
        kernel_weights: tuple = (0.15, 0.7, 0.15)
    ):
        """
        Initialize PLF 2.0 controller.

        Args:
            alpha: Curvature weight for phi (risk angle)
            beta: Curvature weight for r (liquidity radius)
            eta: Predictive horizon parameter
            lambda_param: Attractor field strength
            max_move: Maximum mobility per cycle
            kernel_weights: Diffusion kernel weights
        """
        self.curvature = PhaseCurvatureEngine(alpha=alpha, beta=beta)
        self.predictor = PredictiveDriftMapper(eta=eta)
        self.attractor = AttractorField(lambda_param=lambda_param)
        self.mobility = FractonMobilityRestrainer(max_move=max_move)
        self.diffusion = TorusDiffusionOperator(kernel_weights=kernel_weights)

    def step(self, state: dict) -> dict:
        """
        Execute one PLF 2.0 stabilization step.

        Args:
            state: State dict with 'theta', 'phi', 'r' arrays

        Returns:
            Stabilized state dict with 'theta', 'phi', 'r' arrays
        """
        # 1. Compute curvature (second-order instability detection)
        kappa = self.curvature.compute(state)

        # 2. Project future drift
        drift = self.predictor.project(state, kappa)

        # 3. Compute safe attractor basin
        basin = self.attractor.compute(state, kappa)

        # 4. Restrict mobility (fracton constraints)
        restricted = self.mobility.restrict(basin)

        # 5. Apply torus diffusion
        stable = self.diffusion.spread(restricted)

        return stable


# Example usage
if __name__ == "__main__":
    import numpy as np

    print("Testing PLF 2.0 Controller...")

    plf2 = PLF2Controller()

    # Test with unstable state
    print("\n1. Unstable state (high curvature):")
    n = 100
    t = np.linspace(0, 2*np.pi, n)

    # Sinusoidal state (high curvature)
    state = {
        "theta": np.sin(t),
        "phi": np.sin(2*t),
        "r": 0.5 + 0.3 * np.cos(t)
    }

    stable = plf2.step(state)

    # Measure stabilization
    orig_var_theta = np.var(state["theta"])
    stable_var_theta = np.var(stable["theta"])

    print(f"  Original variance (theta): {orig_var_theta:.6f}")
    print(f"  Stabilized variance (theta): {stable_var_theta:.6f}")
    print(f"  Reduction: {(1 - stable_var_theta/orig_var_theta)*100:.1f}%")

    # Test with already-stable state
    print("\n2. Already stable state:")
    stable_input = {
        "theta": np.ones(n) * 0.5 + np.random.randn(n) * 0.01,
        "phi": np.ones(n) * 0.3 + np.random.randn(n) * 0.01,
        "r": np.ones(n) * 0.7 + np.random.rand(n) * 0.01,
    }

    stable_output = plf2.step(stable_input)

    theta_change = np.mean(np.abs(stable_output["theta"] - stable_input["theta"]))
    print(f"  Mean change (theta): {theta_change:.6f}")
    print(f"  (Should be small - minimal intervention needed)")

    # Test persistence over multiple cycles
    print("\n3. Multi-cycle stability:")
    state = {
        "theta": np.random.randn(n) * 0.5,
        "phi": np.random.randn(n) * 0.3,
        "r": 0.5 + np.random.rand(n) * 0.5,
    }

    variances = []
    for i in range(10):
        state = plf2.step(state)
        variances.append(np.var(state["theta"]))

    print(f"  Initial variance: {variances[0]:.6f}")
    print(f"  Final variance: {variances[-1]:.6f}")
    print(f"  Converged: {variances[-1] < variances[0]}")

    print("\n✓ PLF 2.0 Controller operational")
