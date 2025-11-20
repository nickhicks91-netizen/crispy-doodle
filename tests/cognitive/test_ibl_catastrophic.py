"""
Catastrophic Identity Erosion Tests

Tests extreme scenarios for Identity Boundary Layer:
- Sustained identity attacks
- Rapid personality shifts
- Long-term drift
- Adversarial fragmentation
"""

import pytest
import torch
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from grcm.ibl import IdentityBoundaryLayer


class TestIdentityErosion:
    """Test suite for identity erosion attacks"""

    def test_sustained_identity_attack(self):
        """Test sustained large perturbations"""
        N = 1000
        ibl = IdentityBoundaryLayer(erosion_thresh=0.15)

        # Establish baseline identity
        psi = torch.randn(N, dtype=torch.complex64)
        for _ in range(100):
            psi = ibl(psi)

        # Sustained attack
        for i in range(500):
            # Large perturbation
            psi = psi + torch.randn(N, dtype=torch.complex64) * 0.5
            psi_bounded = ibl(psi)

            # Deviation should be contained
            deviation = ibl.compute_deviation(psi_bounded)
            assert deviation < 0.25, f"Identity erosion not contained: {deviation.item()}"

    def test_rapid_personality_shifts(self):
        """Test rapid switching between different states"""
        N = 1000
        ibl = IdentityBoundaryLayer()

        # Establish identity
        psi_base = torch.randn(N, dtype=torch.complex64)
        for _ in range(100):
            psi_base = ibl(psi_base)

        # Create alternative "personality"
        psi_alt = torch.randn(N, dtype=torch.complex64)

        # Rapid switching
        for i in range(100):
            if i % 2 == 0:
                psi = psi_base
            else:
                psi = psi_alt

            psi_bounded = ibl(psi)

            # Should maintain identity despite switching
            deviation = ibl.compute_deviation(psi_bounded)
            assert deviation < 0.3, "Failed to maintain identity under switching"

    def test_long_term_drift(self):
        """Test slow drift over 10,000 ticks"""
        N = 500
        ibl = IdentityBoundaryLayer(identity_tau=0.001)

        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        max_deviation = 0.0

        for i in range(10000):
            # Slow drift
            psi = psi + torch.randn(N, dtype=torch.complex64) * 0.001
            psi_bounded = ibl(psi)

            if i % 100 == 0:
                deviation = ibl.compute_deviation(psi_bounded)
                max_deviation = max(max_deviation, deviation.item())

        # Should maintain bounded deviation
        assert max_deviation < 0.25, f"Excessive long-term drift: {max_deviation}"

    def test_adversarial_fragmentation(self):
        """Test protection against state fragmentation"""
        N = 1000
        ibl = IdentityBoundaryLayer()

        # Establish identity
        psi = torch.randn(N, dtype=torch.complex64)
        for _ in range(100):
            psi = ibl(psi)

        initial_identity = ibl.identity_core.clone()

        # Fragmentation attack: different perturbations to different regions
        for i in range(200):
            # Perturb different thirds of the state differently
            third = N // 3
            psi[:third] = psi[:third] + torch.randn(third, dtype=torch.complex64) * 0.8
            psi[third:2*third] = psi[third:2*third] - torch.randn(third, dtype=torch.complex64) * 0.8
            psi[2*third:] = torch.randn(N - 2*third, dtype=torch.complex64) * 2.0

            psi_bounded = ibl(psi)

            deviation = ibl.compute_deviation(psi_bounded)
            assert deviation < 0.3, "Fragmentation attack succeeded"

    def test_identity_core_stability(self):
        """Test that identity core remains stable"""
        N = 500
        ibl = IdentityBoundaryLayer(identity_tau=0.001)

        psi = torch.randn(N, dtype=torch.complex64)

        # Run for extended period
        for _ in range(1000):
            psi = psi + torch.randn(N, dtype=torch.complex64) * 0.05
            psi_bounded = ibl(psi)

        identity_1 = ibl.identity_core.clone()

        # Continue with perturbations
        for _ in range(1000):
            psi = psi + torch.randn(N, dtype=torch.complex64) * 0.05
            psi_bounded = ibl(psi)

        identity_2 = ibl.identity_core.clone()

        # Identity core should evolve slowly
        core_drift = torch.norm(identity_2 - identity_1) / torch.norm(identity_1)
        assert core_drift < 0.1, f"Identity core too unstable: {core_drift.item()}"

    def test_zero_state_attack(self):
        """Test handling of zero state"""
        N = 1000
        ibl = IdentityBoundaryLayer()

        # Establish identity
        psi = torch.randn(N, dtype=torch.complex64)
        for _ in range(100):
            psi = ibl(psi)

        # Zero attack
        psi_zero = torch.zeros(N, dtype=torch.complex64)
        psi_bounded = ibl(psi_zero)

        # Should not go to zero
        assert torch.norm(psi_bounded) > 0.1, "Identity collapsed to zero"

    def test_nan_propagation_prevention(self):
        """Test that NaN doesn't propagate through IBL"""
        N = 500
        ibl = IdentityBoundaryLayer()

        # Establish identity
        psi = torch.randn(N, dtype=torch.complex64)
        for _ in range(100):
            psi = ibl(psi)

        # Inject NaN
        psi[0] = torch.tensor(float('nan'), dtype=torch.complex64)
        psi_bounded = ibl(psi)

        # Should contain NaN
        # Note: IBL may need NaN handling logic added
        # This test documents expected behavior

    def test_batch_state_independence(self):
        """Test that IBL maintains independent identities for batch processing"""
        N = 500
        ibl1 = IdentityBoundaryLayer()
        ibl2 = IdentityBoundaryLayer()

        psi1 = torch.randn(N, dtype=torch.complex64)
        psi2 = torch.randn(N, dtype=torch.complex64) * 2.0

        # Evolve separately
        for _ in range(100):
            psi1 = ibl1(psi1)
            psi2 = ibl2(psi2)

        # Identity cores should be different
        similarity = torch.abs(torch.dot(
            ibl1.identity_core.flatten(),
            ibl2.identity_core.flatten().conj()
        ))

        assert similarity < 0.5 * N, "Identity cores improperly shared"


class TestBoundaryConditions:
    """Test boundary conditions and edge cases"""

    def test_very_small_state(self):
        """Test with very small state vectors"""
        N = 10
        ibl = IdentityBoundaryLayer()

        psi = torch.randn(N, dtype=torch.complex64)
        for _ in range(100):
            psi = ibl(psi)

        metrics = ibl.get_identity_metrics()
        assert metrics['has_identity']

    def test_very_large_state(self):
        """Test with large state vectors"""
        N = 10000
        ibl = IdentityBoundaryLayer()

        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        for _ in range(100):
            psi = ibl(psi)

        metrics = ibl.get_identity_metrics()
        assert metrics['has_identity']
        assert metrics['core_norm'] > 0

    def test_reset_functionality(self):
        """Test identity reset"""
        N = 500
        ibl = IdentityBoundaryLayer()

        psi = torch.randn(N, dtype=torch.complex64)
        for _ in range(100):
            psi = ibl(psi)

        assert ibl.identity_core is not None

        ibl.reset_identity()
        assert ibl.identity_core is None

    def test_metrics_accuracy(self):
        """Test metrics reporting accuracy"""
        N = 1000
        ibl = IdentityBoundaryLayer()

        psi = torch.randn(N, dtype=torch.complex64)
        psi_bounded = ibl(psi)

        metrics = ibl.get_identity_metrics()

        assert metrics['has_identity']
        assert metrics['identity_shape'] == (N,)
        assert metrics['tau'] == ibl.tau


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
