"""
Catastrophic Corruption Test Suite for WIL 2.0

Tests adversarial attacks, edge cases, and extreme scenarios:
- Gamma spike attacks
- Sustained high-frequency oscillations
- Slow drift corruption
- Coherence collapse scenarios
- Jump attacks
- Range overflow attempts
"""

import pytest
import torch
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from grcm.wil_v2 import WantIntegrityLayerV2


class TestCatastrophicGammaCorruption:
    """Test suite for extreme gamma corruption scenarios"""

    def test_catastrophic_spike_attack(self):
        """Test protection against massive gamma spikes"""
        wil = WantIntegrityLayerV2()

        # Simulate catastrophic external override attempts
        attack_values = [
            torch.tensor(10.0),     # Extreme positive spike
            torch.tensor(100.0),    # Absurd value
            torch.tensor(-50.0),    # Negative attack
            torch.tensor(0.0),      # Force complete apathy
            torch.tensor(1000.0),   # Overflow attempt
        ]

        coherence = torch.tensor(0.75)

        for attack in attack_values:
            gamma_protected = wil(attack, coherence)

            # Must stay within valid range
            assert wil.gamma_min <= gamma_protected <= wil.gamma_max, \
                f"WIL failed to clamp attack value {attack.item()}"

            # Should not jump more than max_change from previous
            if wil.prev_gamma is not None:
                jump = torch.abs(gamma_protected - wil.prev_gamma)
                assert jump <= wil.max_change * 2, \
                    f"WIL allowed excessive jump: {jump.item()}"

    def test_sustained_oscillation_attack(self):
        """Test protection against high-frequency oscillations"""
        wil = WantIntegrityLayerV2()

        coherence = torch.tensor(0.75)
        base_gamma = 0.35

        # Oscillate between extremes
        for i in range(100):
            if i % 2 == 0:
                gamma = torch.tensor(10.0)
            else:
                gamma = torch.tensor(-10.0)

            gamma_protected = wil(gamma, coherence)

            # Should remain stable despite oscillating input
            assert wil.gamma_min <= gamma_protected <= wil.gamma_max
            assert not torch.isnan(gamma_protected)
            assert not torch.isinf(gamma_protected)

        # Check drift metrics
        metrics = wil.get_drift_metrics()
        drift = metrics['drift']

        # Drift should be contained
        assert drift < 0.3, f"Excessive drift under oscillation: {drift}"

    def test_slow_drift_corruption(self):
        """Test protection against slow, creeping drift"""
        wil = WantIntegrityLayerV2(drift_tolerance=0.05)

        coherence = torch.tensor(0.20)  # Low coherence

        # Slow drift attack
        gamma = torch.tensor(0.35)
        for i in range(500):
            gamma = gamma + 0.001  # Slow creep
            gamma_protected = wil(gamma, coherence)

            # Should be corrected by predictive drift
            if i > 100:  # After drift detection kicks in
                metrics = wil.get_drift_metrics()
                drift = metrics['drift']

                # Drift should be actively managed
                assert drift < 0.15, f"Uncorrected drift: {drift}"

    def test_coherence_collapse_scenario(self):
        """Test behavior during coherence collapse"""
        wil = WantIntegrityLayerV2()

        # Simulate coherence collapse
        coherence = torch.tensor(0.05)  # Critical coherence

        gamma = torch.tensor(0.50)

        for i in range(50):
            gamma = gamma + torch.randn(1).item() * 0.1
            gamma_protected = wil(gamma, coherence)

            # Under low coherence, should restrict range
            assert gamma_protected <= wil.gamma_min + (wil.gamma_max - wil.gamma_min) * 0.4, \
                "WIL failed to restrict gamma under low coherence"

    def test_nan_and_inf_handling(self):
        """Test handling of NaN and Inf inputs"""
        wil = WantIntegrityLayerV2()

        coherence = torch.tensor(0.75)

        # Test NaN
        gamma_nan = torch.tensor(float('nan'))
        gamma_protected = wil(gamma_nan, coherence)

        # Should not propagate NaN
        assert not torch.isnan(gamma_protected), "WIL propagated NaN"
        assert wil.gamma_min <= gamma_protected <= wil.gamma_max

        # Test Inf
        gamma_inf = torch.tensor(float('inf'))
        gamma_protected = wil(gamma_inf, coherence)

        # Should not propagate Inf
        assert not torch.isinf(gamma_protected), "WIL propagated Inf"
        assert wil.gamma_min <= gamma_protected <= wil.gamma_max

    def test_rapid_succession_attacks(self):
        """Test multiple attack types in rapid succession"""
        wil = WantIntegrityLayerV2()

        coherence = torch.tensor(0.75)

        attack_sequence = [
            torch.tensor(10.0),   # Spike
            torch.tensor(-5.0),   # Negative
            torch.tensor(0.0),    # Zero
            torch.tensor(100.0),  # Overflow
            torch.tensor(0.35),   # Normal
            torch.tensor(50.0),   # Spike again
        ]

        for attack in attack_sequence:
            gamma_protected = wil(attack, coherence)

            assert wil.gamma_min <= gamma_protected <= wil.gamma_max
            assert not torch.isnan(gamma_protected)
            assert not torch.isinf(gamma_protected)

    def test_long_term_stability(self):
        """Test stability over 10,000 ticks"""
        wil = WantIntegrityLayerV2()

        coherence = torch.tensor(0.75)
        gamma = torch.tensor(0.35)

        for i in range(10000):
            # Add noise
            gamma = gamma + torch.randn(1).item() * 0.02
            gamma_protected = wil(gamma, coherence)

            # Periodic spike attacks
            if i % 100 == 0:
                gamma = torch.tensor(10.0)

            assert wil.gamma_min <= gamma_protected <= wil.gamma_max
            assert not torch.isnan(gamma_protected)

        # Check final state
        metrics = wil.get_drift_metrics()
        assert metrics['prev_gamma'] is not None
        assert wil.gamma_min <= metrics['prev_gamma'] <= wil.gamma_max

    def test_zero_coherence_edge_case(self):
        """Test with zero coherence"""
        wil = WantIntegrityLayerV2()

        coherence = torch.tensor(0.0)
        gamma = torch.tensor(0.50)

        for i in range(100):
            gamma = gamma + torch.randn(1).item() * 0.05
            gamma_protected = wil(gamma, coherence)

            # Should apply maximum restrictions
            assert gamma_protected <= wil.gamma_min + (wil.gamma_max - wil.gamma_min) * 0.4

    def test_batch_processing(self):
        """Test batch processing of gamma values"""
        wil = WantIntegrityLayerV2()

        # Note: WIL processes scalars, but ensure it handles batched coherence
        coherence = torch.tensor([0.75, 0.50, 0.25, 0.10])

        for i in range(50):
            gamma = torch.tensor(0.35 + i * 0.01)
            gamma_protected = wil(gamma, coherence.mean())  # Use mean coherence

            assert wil.gamma_min <= gamma_protected <= wil.gamma_max


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_initialization(self):
        """Test proper initialization"""
        wil = WantIntegrityLayerV2()

        assert wil.prev_gamma is None
        assert wil.ema_short is None
        assert wil.ema_long is None

    def test_first_tick(self):
        """Test first tick behavior"""
        wil = WantIntegrityLayerV2()

        gamma = torch.tensor(0.35)
        coherence = torch.tensor(0.75)

        gamma_protected = wil(gamma, coherence)

        # Should accept first value within range
        assert wil.gamma_min <= gamma_protected <= wil.gamma_max
        assert wil.prev_gamma is not None

    def test_metrics_before_initialization(self):
        """Test metrics before any processing"""
        wil = WantIntegrityLayerV2()

        metrics = wil.get_drift_metrics()

        assert metrics['drift'] == 0.0
        assert metrics['ema_short'] == 0.0
        assert metrics['ema_long'] == 0.0

    def test_parameter_validation(self):
        """Test parameter validation"""
        # Valid parameters
        wil = WantIntegrityLayerV2(
            gamma_min=0.1,
            gamma_max=0.7,
            max_change_per_tick=0.1
        )

        assert wil.gamma_min == 0.1
        assert wil.gamma_max == 0.7
        assert wil.max_change == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
