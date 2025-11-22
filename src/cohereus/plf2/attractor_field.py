"""
Attractor Field — Safe Basin Computation

Computes safe target attractor basins based on curvature signatures.
High curvature regions are pulled back toward stable manifolds.

DNA Source: EchoZero stillness recentering principle
"""

import numpy as np


class AttractorField:
    """
    Computes safe target attractor basins based on curvature signatures.

    When curvature is high (system bending toward instability),
    the attractor field pulls the state back toward a stable basin.
    """

    def __init__(self, lambda_param: float = 0.15):
        """
        Initialize attractor field generator.

        Args:
            lambda_param: Attraction strength toward safe basin
        """
        self.lam = lambda_param

    def compute(self, state: dict, curvature: np.ndarray) -> dict:
        """
        Compute safe attractor basin.

        Args:
            state: Current state dict
            curvature: Curvature vector (instability measure)

        Returns:
            Dictionary with basin coordinates for each dimension
        """
        theta = state["theta"]
        phi = state["phi"]
        r = state["r"]

        # Basin = current state - lambda * curvature
        # High curvature → larger correction
        basin_theta = theta - self.lam * curvature
        basin_phi = phi - self.lam * curvature * 0.7
        basin_r = r - self.lam * curvature * 0.4

        return {
            "theta_basin": basin_theta,
            "phi_basin": basin_phi,
            "r_basin": basin_r
        }


# Example usage
if __name__ == "__main__":
    print("Testing Attractor Field...")

    field = AttractorField(lambda_param=0.15)

    # Test with high curvature state
    print("\n1. High curvature (unstable):")
    n = 100
    state = {
        "theta": np.random.randn(n) * 0.5,
        "phi": np.random.randn(n) * 0.3,
        "r": np.random.rand(n) * 0.5 + 0.5,
    }

    # High curvature
    curvature = np.random.randn(n) * 2.0

    basin = field.compute(state, curvature)

    theta_diff = np.mean(np.abs(basin["theta_basin"] - state["theta"]))
    print(f"  Mean correction (theta): {theta_diff:.6f}")
    print(f"  (Should be significant due to high curvature)")

    # Test with low curvature state
    print("\n2. Low curvature (stable):")
    curvature_low = np.random.randn(n) * 0.1

    basin_stable = field.compute(state, curvature_low)

    theta_diff_stable = np.mean(np.abs(basin_stable["theta_basin"] - state["theta"]))
    print(f"  Mean correction (theta): {theta_diff_stable:.6f}")
    print(f"  (Should be small due to low curvature)")

    print("\n✓ Attractor field operational")
