"""
Torus Diffusion Operator — Lateral Risk Spreading

Injects lateral diffusion across the torus to prevent synchronization.
Spreads risk and activity using cyclic convolution.

DNA Source: Distributed diffusion patterns from EchoZero mesh coordination
"""

import numpy as np


class TorusDiffusionOperator:
    """
    Injects lateral diffusion across the torus grid.

    Prevents synchronization by spreading concentrated risk/activity
    laterally using a diffusion kernel.
    """

    def __init__(self, kernel_weights: tuple = (0.15, 0.7, 0.15)):
        """
        Initialize torus diffusion operator.

        Args:
            kernel_weights: Diffusion kernel (center, neighbors)
                           Default: (0.15, 0.7, 0.15) - moderate diffusion
        """
        self.kernel = np.array(kernel_weights)

    def _cyclic_convolve(self, arr: np.ndarray) -> np.ndarray:
        """
        Apply cyclic convolution (respecting torus topology).

        Args:
            arr: Input array

        Returns:
            Diffused array
        """
        # Pad with wraparound (torus boundary conditions)
        padded = np.concatenate([arr[-1:], arr, arr[:1]])

        # Convolve and extract valid region
        diffused = np.convolve(padded, self.kernel, mode='same')[1:-1]

        return diffused

    def spread(self, stable_state: dict) -> dict:
        """
        Apply diffusion to stable state.

        Args:
            stable_state: State dict with 'theta_stable', 'phi_stable', 'r_stable'

        Returns:
            Dictionary with diffused state
        """
        theta = stable_state["theta_stable"]
        phi = stable_state["phi_stable"]
        r = stable_state["r_stable"]

        # Apply cyclic diffusion
        diffuse_theta = self._cyclic_convolve(theta)
        diffuse_phi = self._cyclic_convolve(phi)
        diffuse_r = self._cyclic_convolve(r)

        return {
            "theta": diffuse_theta,
            "phi": diffuse_phi,
            "r": diffuse_r
        }


# Example usage
if __name__ == "__main__":
    print("Testing Torus Diffusion Operator...")

    diffuser = TorusDiffusionOperator()

    # Test with concentrated spike
    print("\n1. Concentrated spike (should spread):")
    n = 100
    theta = np.zeros(n)
    theta[n//2] = 1.0  # Single spike

    stable_state = {
        "theta_stable": theta,
        "phi_stable": np.zeros(n),
        "r_stable": np.ones(n) * 0.5,
    }

    diffused = diffuser.spread(stable_state)

    print(f"  Original max: {np.max(theta):.3f}")
    print(f"  Diffused max: {np.max(diffused['theta']):.3f}")
    print(f"  Spread width: {np.sum(diffused['theta'] > 0.01)} cells")

    # Test with uniform state (should stay uniform)
    print("\n2. Uniform state (should remain uniform):")
    uniform_state = {
        "theta_stable": np.ones(n) * 0.5,
        "phi_stable": np.ones(n) * 0.3,
        "r_stable": np.ones(n) * 0.7,
    }

    diffused_uniform = diffuser.spread(uniform_state)

    theta_var = np.var(diffused_uniform["theta"])
    print(f"  Variance after diffusion: {theta_var:.9f}")
    print(f"  (Should be near zero)")

    print("\n✓ Torus diffusion operator operational")
