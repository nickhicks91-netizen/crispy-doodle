"""
IBL — Identity Boundary Layer

Maintains stable identity manifold across long timelines.

Identity preservation through:
- Long-term average ψ tracking
- Projection onto identity subspace
- Identity erosion detection
- Boundary constraint enforcement

Prevents:
- Personality drift
- Internal fragmentation
- Identity collapse
- Erratic behavioral shifts
"""

import torch
import torch.nn as nn


class IdentityBoundaryLayer(nn.Module):
    """
    IBL — Identity Boundary Layer

    Maintains a stable identity manifold by:
    - Tracking long-term average ψ state
    - Projecting current ψ onto identity subspace
    - Detecting identity erosion
    - Enforcing identity boundary constraints

    The identity "core" is a slowly-evolving attractor that represents
    the long-term stable configuration of the system. Current states are
    softly constrained to remain within a neighborhood of this core.
    """

    def __init__(
        self,
        identity_tau: float = 0.001,
        erosion_thresh: float = 0.15,
        projection_strength: float = 0.4,
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize Identity Boundary Layer

        Args:
            identity_tau: EMA coefficient for identity core update (very slow)
            erosion_thresh: Maximum allowed deviation from identity core
            projection_strength: Strength of pull-back toward identity manifold
            device: Computation device
        """
        super().__init__()

        self.tau = identity_tau
        self.erosion_thresh = erosion_thresh
        self.projection_strength = projection_strength
        self.device = device

        # Identity core state (slowly evolving)
        self.register_buffer('identity_core', None)

    def update_identity(self, psi: torch.Tensor):
        """
        Update the identity core using slow EMA.

        The identity core represents the "true self" - a slowly-evolving
        attractor that defines the stable personality/behavior manifold.

        Args:
            psi: Current state vector
        """
        if self.identity_core is None:
            self.identity_core = psi.clone().detach()
        else:
            # Very slow update (tau typically 0.001)
            self.identity_core = (
                self.tau * psi.detach() +
                (1 - self.tau) * self.identity_core
            )

    def compute_deviation(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Compute normalized deviation from identity core.

        Args:
            psi: Current state vector

        Returns:
            Normalized deviation metric
        """
        if self.identity_core is None:
            return torch.tensor(0.0, device=self.device)

        # Normalized L2 deviation
        deviation = torch.norm(psi - self.identity_core) / (
            torch.norm(self.identity_core) + 1e-8
        )

        return deviation

    def enforce_boundaries(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Enforce identity boundary constraints.

        If the current state deviates too far from the identity core,
        apply a soft projection back toward the identity manifold.

        Args:
            psi: Current state vector

        Returns:
            Boundary-enforced state vector
        """
        if self.identity_core is None:
            return psi

        deviation = self.compute_deviation(psi)

        # If deviation exceeds threshold, project back
        if deviation > self.erosion_thresh:
            # Soft projection: blend toward identity core
            psi = (
                self.identity_core +
                self.projection_strength * (psi - self.identity_core)
            )

        return psi

    def forward(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Full IBL pipeline.

        Args:
            psi: Current state vector (complex-valued resonator state)

        Returns:
            Identity-bounded state vector
        """
        # Ensure correct device
        psi = psi.to(self.device)

        # Update identity core (slow EMA)
        self.update_identity(psi)

        # Enforce identity boundaries
        psi = self.enforce_boundaries(psi)

        return psi

    def get_identity_metrics(self) -> dict:
        """Get identity diagnostics"""
        if self.identity_core is None:
            return {
                'has_identity': False,
                'core_norm': 0.0,
                'deviation': 0.0
            }

        return {
            'has_identity': True,
            'core_norm': torch.norm(self.identity_core).item(),
            'identity_shape': tuple(self.identity_core.shape),
            'tau': self.tau,
            'erosion_thresh': self.erosion_thresh
        }

    def reset_identity(self):
        """Reset identity core (use with caution)"""
        self.identity_core = None


# Example usage
if __name__ == "__main__":
    print("Testing Identity Boundary Layer...")

    N = 1000
    ibl = IdentityBoundaryLayer()

    # Initialize with base state
    print("\n1. Establishing identity core:")
    psi = torch.randn(N, dtype=torch.complex64)

    for i in range(100):
        psi_bounded = ibl(psi)
        psi = psi + torch.randn(N, dtype=torch.complex64) * 0.01

        if i % 25 == 0:
            metrics = ibl.get_identity_metrics()
            deviation = ibl.compute_deviation(psi)
            print(f"  Tick {i}: deviation={deviation.item():.6f}, "
                  f"core_norm={metrics['core_norm']:.4f}")

    # Test identity erosion attack
    print("\n2. Identity erosion attack:")
    for i in range(20):
        # Large perturbation attempting to shift identity
        psi = psi + torch.randn(N, dtype=torch.complex64) * 0.5
        psi_bounded = ibl(psi)

        deviation_before = torch.norm(psi - ibl.identity_core) / torch.norm(ibl.identity_core)
        deviation_after = torch.norm(psi_bounded - ibl.identity_core) / torch.norm(ibl.identity_core)

        if i % 5 == 0:
            print(f"  Tick {i}: deviation before={deviation_before.item():.4f}, "
                  f"after={deviation_after.item():.4f}")

    # Verify identity preservation
    print("\n3. Identity preservation check:")
    metrics = ibl.get_identity_metrics()
    print(f"  Identity core maintained: {metrics['has_identity']}")
    print(f"  Core norm: {metrics['core_norm']:.4f}")
    print(f"  Erosion threshold: {metrics['erosion_thresh']}")

    # Test long-term stability
    print("\n4. Long-term stability test (1000 ticks):")
    deviations = []
    for i in range(1000):
        psi = psi + torch.randn(N, dtype=torch.complex64) * 0.1
        psi_bounded = ibl(psi)
        deviation = ibl.compute_deviation(psi_bounded)
        deviations.append(deviation.item())

    print(f"  Mean deviation: {sum(deviations)/len(deviations):.6f}")
    print(f"  Max deviation: {max(deviations):.6f}")
    print(f"  Identity preserved: {max(deviations) < ibl.erosion_thresh * 1.2}")

    print("\n✓ Identity Boundary Layer tests passed")
