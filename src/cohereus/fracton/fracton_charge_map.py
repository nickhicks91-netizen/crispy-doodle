"""
Fracton Charge Map — Mobility Cost Assignment

Assigns 'fracton charge' to each account based on local stress.
Higher charge → lower allowable mobility.

Charge = curvature + liquidity pressure
"""

import numpy as np


class FractonChargeMap:
    """
    Assigns fracton charge to each account/cohort.

    Charge indicates mobility cost:
    - High charge = high local stress = restricted movement
    - Low charge = low stress = free movement

    This creates geometry where harmful moves become "expensive".
    """

    def compute_charge(self, state: dict) -> np.ndarray:
        """
        Compute fracton charge from state.

        Args:
            state: State dict with 'theta', 'phi', 'r'

        Returns:
            Charge array [0, 1] (higher = more restricted)
        """
        theta = state["theta"]
        phi = state["phi"]
        r = state["r"]

        # Charge = local stress indicator
        # Curvature + deviation from mean
        curvature = (
            np.gradient(np.gradient(theta))
            + 0.7 * np.gradient(np.gradient(phi))
            + 0.4 * np.gradient(np.gradient(r))
        )

        # Add liquidity pressure (deviation from mean)
        pressure = (r - np.mean(r)) ** 2

        # Combined charge
        charge = np.abs(curvature) + pressure

        # Normalize to [0, 1]
        charge = charge / (np.max(charge) + 1e-9)

        return charge


# Example usage
if __name__ == "__main__":
    print("Testing Fracton Charge Map...")

    charge_map = FractonChargeMap()

    # Test with low-stress state
    print("\n1. Low-stress state:")
    n = 100
    state = {
        "theta": np.ones(n) * 0.5 + np.random.randn(n) * 0.01,
        "phi": np.ones(n) * 0.3 + np.random.randn(n) * 0.01,
        "r": np.ones(n) * 0.7 + np.random.rand(n) * 0.01,
    }

    charge = charge_map.compute_charge(state)
    print(f"  Mean charge: {np.mean(charge):.6f}")
    print(f"  Max charge: {np.max(charge):.6f}")

    # Test with high-stress state
    print("\n2. High-stress state:")
    t = np.linspace(0, 2*np.pi, n)
    state_stressed = {
        "theta": np.sin(t) * 2,  # High curvature
        "phi": np.sin(2*t),
        "r": 0.5 + np.random.rand(n),  # High variance
    }

    charge_stressed = charge_map.compute_charge(state_stressed)
    print(f"  Mean charge: {np.mean(charge_stressed):.6f}")
    print(f"  Max charge: {np.max(charge_stressed):.6f}")
    print(f"  (Should be higher than low-stress case)")

    print("\n✓ Fracton charge map operational")
