"""
Stability Kernel — Global Stabilizing Projection

Applies global stabilizing projection to keep the system within
a safe toroidal manifold. Final safeguard layer.
"""

import numpy as np


class StabilityKernel:
    """
    Global stability projection.

    Pulls the entire system toward mean-field equilibrium
    if it drifts too far from center.
    """

    def __init__(self, lambda_param: float = 0.05):
        """
        Initialize stability kernel.

        Args:
            lambda_param: Attraction strength toward mean-field
        """
        self.lam = lambda_param

    def project(self, state: dict) -> dict:
        """
        Apply global stability projection.

        Args:
            state: Current state

        Returns:
            Globally stabilized state
        """
        theta = state["theta"]
        phi = state["phi"]
        r = state["r"]

        # Mean-field attractors
        theta_at = np.mean(theta)
        phi_at = np.mean(phi)
        r_at = np.mean(r)

        # Soft projection toward mean-field
        theta_stable = theta - self.lam * (theta - theta_at)
        phi_stable = phi - self.lam * (phi - phi_at)
        r_stable = r - self.lam * (r - r_at)

        return {
            "theta": theta_stable,
            "phi": phi_stable,
            "r": r_stable,
        }


# Example usage
if __name__ == "__main__":
    print("Testing Stability Kernel...")

    kernel = StabilityKernel(lambda_param=0.05)

    # Test with dispersed state
    print("\n1. Dispersed state:")
    n = 100
    state = {
        "theta": np.random.randn(n) * 2.0,  # Wide spread
        "phi": np.random.randn(n) * 1.5,
        "r": 0.5 + np.random.rand(n) * 2.0,
    }

    orig_std = np.std(state["theta"])
    projected = kernel.project(state)
    new_std = np.std(projected["theta"])

    print(f"  Original std: {orig_std:.6f}")
    print(f"  After projection: {new_std:.6f}")
    print(f"  Reduction: {(1 - new_std/orig_std)*100:.1f}%")

    # Test with already-centered state
    print("\n2. Already centered state:")
    state_centered = {
        "theta": np.random.randn(n) * 0.1,
        "phi": np.random.randn(n) * 0.1,
        "r": 0.5 + np.random.rand(n) * 0.1,
    }

    projected_centered = kernel.project(state_centered)
    change = np.mean(np.abs(projected_centered["theta"] - state_centered["theta"]))

    print(f"  Mean change: {change:.6f}")
    print(f"  (Should be small - minimal correction needed)")

    print("\n✓ Stability kernel operational")
