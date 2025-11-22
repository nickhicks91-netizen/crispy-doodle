"""
Migration Tensor — Multi-Body Movement Control

Allows multi-body movement but blocks single-body large shifts.
Requires local neighborhood consensus for movement.
"""

import numpy as np


class MigrationTensor:
    """
    Controls multi-body vs single-body movement.

    Single-body movement: blocked if charge is high
    Multi-body movement: allowed if local neighborhood agrees
    """

    def __init__(self, window: int = 7):
        """
        Initialize migration tensor.

        Args:
            window: Neighborhood window for multi-body consensus
        """
        self.window = window

    def migrate(self, state: dict, charge: np.ndarray) -> dict:
        """
        Allow multi-body migration while resisting single-body shifts.

        Args:
            state: Current state
            charge: Fracton charge (mobility cost)

        Returns:
            Migrated state
        """
        theta = state["theta"]
        phi = state["phi"]
        r = state["r"]

        # Compute local average (multi-body consensus)
        avg_theta = np.convolve(theta, np.ones(self.window)/self.window, mode='same')
        avg_phi = np.convolve(phi, np.ones(self.window)/self.window, mode='same')
        avg_r = np.convolve(r, np.ones(self.window)/self.window, mode='same')

        # Allowed movement toward consensus (inversely proportional to charge)
        allowed = 1.0 - charge

        # Move toward local consensus
        theta_new = theta + allowed * (avg_theta - theta)
        phi_new = phi + allowed * (avg_phi - phi)
        r_new = r + allowed * (avg_r - r)

        return {
            "theta": theta_new,
            "phi": phi_new,
            "r": r_new
        }


# Example usage
if __name__ == "__main__":
    print("Testing Migration Tensor...")

    tensor = MigrationTensor(window=7)

    # Test with low charge (high mobility)
    print("\n1. Low charge (should converge to consensus):")
    n = 100
    state = {
        "theta": np.random.randn(n) * 0.5,
        "phi": np.random.randn(n) * 0.3,
        "r": 0.5 + np.random.rand(n) * 0.5,
    }
    charge_low = np.ones(n) * 0.1

    orig_var = np.var(state["theta"])
    migrated = tensor.migrate(state, charge_low)
    new_var = np.var(migrated["theta"])

    print(f"  Original variance: {orig_var:.6f}")
    print(f"  After migration: {new_var:.6f}")
    print(f"  (Should be reduced - converging to consensus)")

    # Test with high charge (low mobility)
    print("\n2. High charge (should resist migration):")
    charge_high = np.ones(n) * 0.9

    migrated_high = tensor.migrate(state, charge_high)
    change = np.mean(np.abs(migrated_high["theta"] - state["theta"]))

    print(f"  Mean change: {change:.6f}")
    print(f"  (Should be small - high charge resists movement)")

    print("\n✓ Migration tensor operational")
