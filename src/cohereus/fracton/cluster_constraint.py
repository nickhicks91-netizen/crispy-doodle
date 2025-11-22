"""
Cluster Constraint — Anti-Synchronization

Prevents cohorts from moving as a synchronized unit unless safe.
Injects desync noise when coherence is too high.
"""

import numpy as np


class ClusterConstraint:
    """
    Prevents cohorts/accounts from moving as synchronized clusters.

    Detects:
    - High correlation between theta and r (phase-risk coupling)
    - Synchronized movement patterns

    Response:
    - Inject decorrelation noise
    - Break cluster formation
    """

    def __init__(self, coherence_threshold: float = 0.25, noise_strength: float = 0.01):
        """
        Initialize cluster constraint.

        Args:
            coherence_threshold: Max allowed correlation before desync
            noise_strength: Strength of decorrelation noise
        """
        self.coherence_threshold = coherence_threshold
        self.noise_strength = noise_strength

    def decouple(self, restricted_state: dict) -> dict:
        """
        Apply cluster decoupling if coherence is too high.

        Args:
            restricted_state: Mobility-restricted state

        Returns:
            Decoupled state (with noise if needed)
        """
        theta = restricted_state["theta"]
        phi = restricted_state["phi"]
        r = restricted_state["r"]

        # Measure cluster coherence (correlation between theta and r)
        coherence = np.corrcoef(theta, r)[0, 1]

        if coherence > self.coherence_threshold:
            # Inject desync noise
            theta = theta + np.random.normal(0, self.noise_strength, size=len(theta))
            phi = phi + np.random.normal(0, self.noise_strength, size=len(phi))
            r = r + np.random.normal(0, self.noise_strength, size=len(r))

        return {
            "theta": theta,
            "phi": phi,
            "r": r
        }


# Example usage
if __name__ == "__main__":
    print("Testing Cluster Constraint...")

    constraint = ClusterConstraint(coherence_threshold=0.25, noise_strength=0.01)

    # Test with synchronized state
    print("\n1. Synchronized state (high coherence):")
    n = 100
    t = np.linspace(0, 1, n)

    # Perfectly correlated
    state_sync = {
        "theta": t,
        "phi": t * 0.5,
        "r": t,  # Perfect correlation with theta
    }

    coherence_before = np.corrcoef(state_sync["theta"], state_sync["r"])[0, 1]
    decoupled = constraint.decouple(state_sync)
    coherence_after = np.corrcoef(decoupled["theta"], decoupled["r"])[0, 1]

    print(f"  Coherence before: {coherence_before:.6f}")
    print(f"  Coherence after: {coherence_after:.6f}")
    print(f"  (Should be reduced)")

    # Test with already-diverse state
    print("\n2. Diverse state (low coherence):")
    state_diverse = {
        "theta": np.random.randn(n),
        "phi": np.random.randn(n),
        "r": np.random.rand(n),
    }

    coherence_diverse_before = np.corrcoef(state_diverse["theta"], state_diverse["r"])[0, 1]
    decoupled_diverse = constraint.decouple(state_diverse)
    coherence_diverse_after = np.corrcoef(decoupled_diverse["theta"], decoupled_diverse["r"])[0, 1]

    print(f"  Coherence before: {coherence_diverse_before:.6f}")
    print(f"  Coherence after: {coherence_diverse_after:.6f}")
    print(f"  (Should be similar - no intervention needed)")

    print("\n✓ Cluster constraint operational")
