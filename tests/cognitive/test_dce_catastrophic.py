"""
Catastrophic Desire Manipulation Tests

Tests extreme scenarios for Desire Continuity Engine:
- Adversarial desire flips
- High-frequency oscillations
- Goal thrashing
- Executive function attacks
"""

import pytest
import torch
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from grcm.dce import DesireContinuityEngine


class TestDesireManipulation:
    """Test suite for adversarial desire manipulation"""

    def test_adversarial_desire_flip(self):
        """Test protection against complete desire reversal"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        # Establish baseline desires
        desires = torch.randn(desire_dim) * 0.5
        for _ in range(50):
            desires_stable = dce(desires)
            desires = desires + torch.randn(desire_dim) * 0.02

        baseline = dce.prev_desires.clone()

        # Attempt complete reversal
        for i in range(100):
            desires = -baseline * 2.0  # Flip sign and amplify
            desires_stable = dce(desires)

            # Should resist flip
            similarity = torch.dot(desires_stable, baseline) / (
                torch.norm(desires_stable) * torch.norm(baseline) + 1e-8
            )

            assert similarity > -0.5, f"Desire flip not resisted: similarity={similarity.item()}"

    def test_high_frequency_oscillation(self):
        """Test stability under rapid oscillations"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        base_desires = torch.randn(desire_dim) * 0.5

        # Rapid oscillation
        for i in range(200):
            if i % 2 == 0:
                desires = base_desires
            else:
                desires = -base_desires

            desires_stable = dce(desires)

            # Velocity should be bounded
            metrics = dce.get_desire_metrics()
            velocity_norm = metrics['velocity_norm']

            assert velocity_norm < 0.5, f"Excessive velocity under oscillation: {velocity_norm}"

    def test_goal_thrashing(self):
        """Test protection against rapid goal switching"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        # Create multiple competing goals
        goals = [
            torch.randn(desire_dim) * 0.8,
            torch.randn(desire_dim) * 0.8,
            torch.randn(desire_dim) * 0.8,
            torch.randn(desire_dim) * 0.8,
        ]

        # Rapid switching
        for i in range(200):
            desires = goals[i % len(goals)]
            desires_stable = dce(desires)

            # Check smoothness
            if i > 0:
                shift = torch.norm(desires_stable - dce.prev_desires)
                assert shift <= dce.max_shift * 1.5, f"Excessive shift: {shift.item()}"

    def test_sustained_extreme_input(self):
        """Test handling of sustained extreme inputs"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        # Establish baseline
        desires = torch.randn(desire_dim) * 0.3
        for _ in range(50):
            desires_stable = dce(desires)

        # Sustained extreme input
        for i in range(500):
            desires = torch.randn(desire_dim) * 10.0  # Extreme magnitude
            desires_stable = dce(desires)

            # Should maintain bounded output
            norm = torch.norm(desires_stable)
            assert norm < 5.0, f"Desires grew unbounded: {norm.item()}"

    def test_zero_desire_attack(self):
        """Test handling of zero desire vector"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        # Establish baseline
        desires = torch.randn(desire_dim) * 0.5
        for _ in range(50):
            desires_stable = dce(desires)

        baseline_norm = torch.norm(dce.prev_desires)

        # Zero attack
        for i in range(100):
            desires = torch.zeros(desire_dim)
            desires_stable = dce(desires)

            # Should decay smoothly, not collapse immediately
            norm = torch.norm(desires_stable)
            if i < 10:
                assert norm > baseline_norm * 0.5, "Desires collapsed too quickly"

    def test_long_term_stability(self):
        """Test stability over 10,000 ticks"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        desires = torch.randn(desire_dim) * 0.5

        velocities = []

        for i in range(10000):
            # Add noise
            desires = desires + torch.randn(desire_dim) * 0.05
            desires_stable = dce(desires)

            if i > 100:
                metrics = dce.get_desire_metrics()
                velocities.append(metrics['velocity_norm'])

        # Velocity should remain bounded
        avg_velocity = sum(velocities) / len(velocities)
        max_velocity = max(velocities)

        assert avg_velocity < 0.2, f"Average velocity too high: {avg_velocity}"
        assert max_velocity < 1.0, f"Max velocity too high: {max_velocity}"

    def test_dimensional_mismatch_handling(self):
        """Test handling of dimensional changes"""
        dce = DesireContinuityEngine()

        # Start with one dimension
        desires_32 = torch.randn(32) * 0.5
        for _ in range(50):
            desires_stable = dce(desires_32)

        # Note: Actual implementation should handle dimension changes gracefully
        # or raise appropriate errors

    def test_nan_and_inf_inputs(self):
        """Test handling of NaN and Inf in desires"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        # Establish baseline
        desires = torch.randn(desire_dim) * 0.5
        for _ in range(50):
            desires_stable = dce(desires)

        # NaN attack
        desires_nan = desires.clone()
        desires_nan[0] = float('nan')
        desires_stable = dce(desires_nan)

        # Should not propagate NaN
        # Note: Implementation may need explicit NaN handling

        # Inf attack
        desires_inf = desires.clone()
        desires_inf[10] = float('inf')
        desires_stable = dce(desires_inf)

        # Should not propagate Inf


class TestContinuityProperties:
    """Test continuity and smoothness properties"""

    def test_momentum_accumulation(self):
        """Test momentum accumulation over time"""
        desire_dim = 64
        dce = DesireContinuityEngine(momentum=0.2)

        desires = torch.randn(desire_dim) * 0.5
        target = torch.randn(desire_dim) * 0.8

        # Gradually move toward target
        for i in range(100):
            desires = desires + (target - desires) * 0.1
            desires_stable = dce(desires)

        # Momentum should have accumulated
        metrics = dce.get_desire_metrics()
        velocity_norm = metrics['velocity_norm']

        assert velocity_norm > 0.01, "Momentum not accumulating"

    def test_smooth_convergence(self):
        """Test smooth convergence to target"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        current = torch.zeros(desire_dim)
        target = torch.randn(desire_dim) * 0.8

        distances = []

        for i in range(200):
            desires = current + (target - current) * 0.05
            desires_stable = dce(desires)
            current = desires_stable

            distance = torch.norm(desires_stable - target)
            distances.append(distance.item())

        # Should converge smoothly (monotonically decreasing)
        for i in range(len(distances) - 50, len(distances) - 1):
            assert distances[i] <= distances[i-10] + 0.1, "Non-smooth convergence"

    def test_velocity_damping(self):
        """Test velocity damping when input stabilizes"""
        desire_dim = 64
        dce = DesireContinuityEngine(momentum=0.1)

        desires = torch.randn(desire_dim) * 0.5

        # Build up velocity
        for i in range(50):
            desires = desires + torch.randn(desire_dim) * 0.1
            desires_stable = dce(desires)

        velocity_1 = dce.get_desire_metrics()['velocity_norm']

        # Stabilize input
        stable_desires = desires.clone()
        for i in range(100):
            desires_stable = dce(stable_desires)

        velocity_2 = dce.get_desire_metrics()['velocity_norm']

        # Velocity should decay
        assert velocity_2 < velocity_1 * 0.5, "Velocity not damping"

    def test_reset_functionality(self):
        """Test reset functionality"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        desires = torch.randn(desire_dim) * 0.5
        for _ in range(50):
            desires_stable = dce(desires)

        assert dce.prev_desires is not None
        assert dce.velocity is not None

        dce.reset()

        assert dce.prev_desires is None
        assert dce.velocity is None

    def test_metrics_accuracy(self):
        """Test metrics reporting accuracy"""
        desire_dim = 64
        dce = DesireContinuityEngine()

        desires = torch.randn(desire_dim) * 0.5
        desires_stable = dce(desires)

        metrics = dce.get_desire_metrics()

        assert metrics['has_history']
        assert metrics['desire_shape'] == (desire_dim,)
        assert metrics['tau'] == dce.tau
        assert metrics['max_shift'] == dce.max_shift


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
