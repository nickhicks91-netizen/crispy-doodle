"""
Mobility Constraint — Individual Movement Limits

Limits individual mobility based on fracton charge.
High charge → low mobility.
"""

import numpy as np


class MobilityConstraint:
    """
    Limits individual account/cohort mobility based on fracton charge.

    Creates energy landscape where:
    - High-charge regions: movement is hard (like moving through mud)
    - Low-charge regions: movement is easy (like ice skating)
    """

    def __init__(self, max_move: float = 0.02):
        """
        Initialize mobility constraint.

        Args:
            max_move: Base mobility cap (2% of manifold radius)
        """
        self.max_move = max_move

    def _clamp(self, x: np.ndarray, limit: np.ndarray) -> np.ndarray:
        """Clamp motion to allowed range per element."""
        delta = x - np.mean(x)
        clamped_delta = np.clip(delta, -limit, limit)
        return np.mean(x) + clamped_delta

    def restrict(self, state: dict, charge: np.ndarray) -> dict:
        """
        Apply mobility constraints based on charge.

        Args:
            state: State dict
            charge: Fracton charge array [0, 1]

        Returns:
            Mobility-restricted state
        """
        theta = state["theta"]
        phi = state["phi"]
        r = state["r"]

        # Allowed movement inversely proportional to charge
        allowed_move = self.max_move * (1.0 - charge)

        # Clamp motion to allowed range
        theta_restricted = self._clamp(theta, allowed_move)
        phi_restricted = self._clamp(phi, allowed_move)
        r_restricted = self._clamp(r, allowed_move)

        return {
            "theta": theta_restricted,
            "phi": phi_restricted,
            "r": r_restricted,
        }


# Example usage
if __name__ == "__main__":
    print("Testing Mobility Constraint...")

    constraint = MobilityConstraint(max_move=0.02)

    # Test with uniform low charge
    print("\n1. Low charge (high mobility):")
    n = 100
    state = {
        "theta": np.random.randn(n) * 0.5,
        "phi": np.random.randn(n) * 0.3,
        "r": 0.5 + np.random.rand(n) * 0.5,
    }
    charge_low = np.ones(n) * 0.1  # Low charge

    restricted_low = constraint.restrict(state, charge_low)
    theta_range_low = np.ptp(restricted_low["theta"])
    print(f"  Theta range: {theta_range_low:.6f}")

    # Test with high charge
    print("\n2. High charge (low mobility):")
    charge_high = np.ones(n) * 0.9  # High charge

    restricted_high = constraint.restrict(state, charge_high)
    theta_range_high = np.ptp(restricted_high["theta"])
    print(f"  Theta range: {theta_range_high:.6f}")
    print(f"  (Should be much smaller than low-charge case)")

    print("\n✓ Mobility constraint operational")
