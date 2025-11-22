"""
Fracton Mobility Restrainer — Constrained Movement

Restrains dangerous motion of capital clusters.
Implements constrained mobility (fracton logic): movement is limited
to prevent rapid collective shifts.

DNA Source: Fracton physics analogy (constrained excitations)
"""

import numpy as np


class FractonMobilityRestrainer:
    """
    Restrains dangerous motion of capital clusters.

    Applies mobility constraints to prevent:
    - Rapid synchronized movements
    - Flash-crash dynamics
    - Collective panic
    """

    def __init__(self, max_move: float = 0.02):
        """
        Initialize fracton mobility restrainer.

        Args:
            max_move: Maximum movement per dimension per cycle (2% of manifold radius)
        """
        self.max_move = max_move

    def _clamp(self, delta: np.ndarray) -> np.ndarray:
        """Clamp movement to maximum allowed."""
        return np.clip(delta, -self.max_move, self.max_move)

    def restrict(self, basin: dict) -> dict:
        """
        Apply mobility constraints to basin coordinates.

        Args:
            basin: Target basin from attractor field

        Returns:
            Dictionary with mobility-restricted coordinates
        """
        theta_b = basin["theta_basin"]
        phi_b = basin["phi_basin"]
        r_b = basin["r_basin"]

        # Compute movement relative to mean (collective center)
        delta_theta = theta_b - np.mean(theta_b)
        delta_phi = phi_b - np.mean(phi_b)
        delta_r = r_b - np.mean(r_b)

        # Apply mobility limits
        stabilized_theta = np.mean(theta_b) + self._clamp(delta_theta)
        stabilized_phi = np.mean(phi_b) + self._clamp(delta_phi)
        stabilized_r = np.mean(r_b) + self._clamp(delta_r)

        return {
            "theta_stable": stabilized_theta,
            "phi_stable": stabilized_phi,
            "r_stable": stabilized_r
        }


# Example usage
if __name__ == "__main__":
    print("Testing Fracton Mobility Restrainer...")

    restrainer = FractonMobilityRestrainer(max_move=0.02)

    # Test with large proposed movement
    print("\n1. Large movement (should be clamped):")
    n = 100
    basin = {
        "theta_basin": np.random.randn(n) * 2.0,  # Large spread
        "phi_basin": np.random.randn(n) * 1.5,
        "r_basin": np.random.rand(n) * 2.0,
    }

    restricted = restrainer.restrict(basin)

    theta_range = np.ptp(restricted["theta_stable"])
    print(f"  Restricted theta range: {theta_range:.6f}")
    print(f"  Max allowed: {restrainer.max_move * 2:.3f}")

    # Test with small proposed movement
    print("\n2. Small movement (should pass through):")
    basin_small = {
        "theta_basin": np.random.randn(n) * 0.01,
        "phi_basin": np.random.randn(n) * 0.01,
        "r_basin": 0.5 + np.random.rand(n) * 0.01,
    }

    restricted_small = restrainer.restrict(basin_small)

    theta_range_small = np.ptp(restricted_small["theta_stable"])
    print(f"  Restricted theta range: {theta_range_small:.6f}")

    print("\n✓ Fracton mobility restrainer operational")
