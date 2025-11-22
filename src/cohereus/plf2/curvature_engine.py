"""
Phase Curvature Engine — Second-Order Stability Detection

Computes curvature (second derivatives) of:
- Phase (theta): Temporal rebalancing timing
- Risk angle (phi): Risk pressure direction
- Liquidity radius (r): Available liquidity

High curvature → bending toward sync or breakdown → predictive warning signal

DNA Source: EchoZero drift curvature (WIL 2.0 predictive correction)
"""

import numpy as np


class PhaseCurvatureEngine:
    """
    Computes second-order curvature for phase, risk angle, and liquidity radius.

    This is the core predictive signal in PLF 2.0.
    First derivative = velocity (drift)
    Second derivative = curvature (acceleration toward instability)

    Tunable weights:
    - alpha: Weight for risk angle curvature
    - beta: Weight for liquidity radius curvature
    """

    def __init__(self, alpha: float = 0.7, beta: float = 0.4):
        """
        Initialize curvature engine.

        Args:
            alpha: Weight for phi (risk angle) curvature
            beta: Weight for r (liquidity radius) curvature
        """
        self.alpha = alpha
        self.beta = beta

    def compute(self, state: dict) -> np.ndarray:
        """
        Compute total curvature from state manifold.

        state: dict with arrays for 'theta', 'phi', 'r'
        Each is shape [N] (cohort_size).

        Returns:
            Curvature vector kappa (shape [N])
        """
        theta = state["theta"]
        phi = state["phi"]
        r = state["r"]

        # First derivatives (velocity/drift)
        d_theta = np.gradient(theta)
        d_phi = np.gradient(phi)
        d_r = np.gradient(r)

        # Second derivatives (curvature/acceleration)
        dd_theta = np.gradient(d_theta)
        dd_phi = np.gradient(d_phi)
        dd_r = np.gradient(d_r)

        # Weighted curvature sum
        kappa = dd_theta + self.alpha * dd_phi + self.beta * dd_r

        return kappa


# Example usage
if __name__ == "__main__":
    print("Testing Phase Curvature Engine...")

    engine = PhaseCurvatureEngine()

    # Test with linear state (zero curvature expected)
    print("\n1. Linear state (zero curvature):")
    n = 100
    state = {
        "theta": np.linspace(0, 1, n),
        "phi": np.linspace(0, 1, n),
        "r": np.linspace(0.5, 1.0, n),
    }

    kappa = engine.compute(state)
    print(f"  Curvature mean: {np.mean(kappa):.6f}")
    print(f"  Curvature std: {np.std(kappa):.6f}")

    # Test with curved state (high curvature expected)
    print("\n2. Sinusoidal state (high curvature):")
    t = np.linspace(0, 2*np.pi, n)
    state = {
        "theta": np.sin(t),
        "phi": np.sin(t * 2),
        "r": 0.5 + 0.3 * np.cos(t),
    }

    kappa = engine.compute(state)
    print(f"  Curvature mean: {np.mean(kappa):.6f}")
    print(f"  Curvature std: {np.std(kappa):.6f}")
    print(f"  Curvature max: {np.max(np.abs(kappa)):.6f}")

    print("\n✓ Curvature engine operational")
