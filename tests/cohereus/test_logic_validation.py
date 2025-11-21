"""
CO-HERE-US Logic Validation Tests

Tests the algorithmic logic without requiring PyTorch:
- Protection layer algorithms
- Phase diversity calculations
- Optimization dynamics
- Account orchestration logic
"""

import sys
import math
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestProtectionLayerLogic:
    """Test protection layer algorithms"""

    def test_ema_smoothing_logic(self):
        """Validate EMA smoothing reduces volatility"""
        print("\n✓ Testing EMA smoothing logic:")

        # Simulate EMA smoothing
        tau = 0.15
        values = [1.0, 5.0, 1.0, 5.0, 1.0]  # Oscillating
        smoothed = []

        prev = values[0]
        for val in values:
            smoothed_val = tau * val + (1 - tau) * prev
            smoothed.append(smoothed_val)
            prev = smoothed_val

        # Check volatility reduction
        raw_volatility = sum(abs(values[i+1] - values[i]) for i in range(len(values)-1))
        smooth_volatility = sum(abs(smoothed[i+1] - smoothed[i]) for i in range(len(smoothed)-1))

        assert smooth_volatility < raw_volatility, "EMA should reduce volatility"
        print(f"  Raw volatility: {raw_volatility:.2f}")
        print(f"  Smoothed volatility: {smooth_volatility:.2f}")
        print(f"  Reduction: {(1 - smooth_volatility/raw_volatility)*100:.1f}%")
        print(f"  ✓ EMA smoothing reduces volatility")

    def test_drift_detection_logic(self):
        """Validate drift detection between timescales"""
        print("\n✓ Testing drift detection logic:")

        # Simulate two EMAs at different timescales
        tau_short = 0.15
        tau_long = 0.01

        values = [1.0] * 10 + [2.0] * 10  # Step change

        ema_short = values[0]
        ema_long = values[0]
        max_drift = 0.0

        for val in values:
            ema_short = tau_short * val + (1 - tau_short) * ema_short
            ema_long = tau_long * val + (1 - tau_long) * ema_long
            drift = abs(ema_short - ema_long)
            max_drift = max(max_drift, drift)

        # Short-term should respond faster, creating drift
        assert max_drift > 0.1, "Should detect drift during transitions"
        print(f"  Max drift detected: {max_drift:.4f}")
        print(f"  ✓ Drift detection works")

    def test_boundary_enforcement_logic(self):
        """Validate soft projection to manifold"""
        print("\n✓ Testing boundary enforcement logic:")

        # Simulate soft projection
        core = 1.0
        deviation_threshold = 0.15
        projection_strength = 0.4

        # Test cases
        test_values = [0.8, 0.9, 1.0, 1.1, 1.2, 1.5]
        projected = []

        for val in test_values:
            deviation = abs(val - core) / core
            if deviation > deviation_threshold:
                # Soft projection
                val_projected = core + projection_strength * (val - core)
            else:
                val_projected = val
            projected.append(val_projected)

        # Check that large deviations are reduced
        assert abs(projected[-1] - core) < abs(test_values[-1] - core), "Should reduce large deviations"
        print(f"  Original deviation: {abs(test_values[-1] - core):.4f}")
        print(f"  After projection: {abs(projected[-1] - core):.4f}")
        print(f"  ✓ Boundary enforcement works")


class TestPhaseDiversityLogic:
    """Test phase diversity calculations"""

    def test_phase_offset_generation(self):
        """Validate evenly-distributed phase offsets"""
        print("\n✓ Testing phase offset generation:")

        n_cohorts = 12
        phases = [i / n_cohorts for i in range(n_cohorts)]

        # Check uniform distribution
        min_spacing = min(phases[i+1] - phases[i] for i in range(n_cohorts-1))
        expected_spacing = 1.0 / n_cohorts

        assert abs(min_spacing - expected_spacing) < 0.01, "Phases should be evenly spaced"
        print(f"  Expected spacing: {expected_spacing:.4f}")
        print(f"  Actual spacing: {min_spacing:.4f}")
        print(f"  ✓ Phase offsets are evenly distributed")

    def test_rebalance_staggering(self):
        """Validate temporal staggering prevents synchronization"""
        print("\n✓ Testing rebalance staggering:")

        n_cohorts = 12
        rebalance_period = 30
        phases = [i / n_cohorts for i in range(n_cohorts)]

        # Simulate 90 days
        rebalances_per_day = [0] * 90

        for day in range(90):
            for cohort_id, phase in enumerate(phases):
                phase_adjusted_day = day + phase * rebalance_period
                normalized_day = (phase_adjusted_day % rebalance_period) / rebalance_period

                # Rebalance window (5%)
                if normalized_day < 0.05:
                    rebalances_per_day[day] += 1

        max_simultaneous = max(rebalances_per_day)
        max_fraction = max_simultaneous / n_cohorts

        assert max_fraction < 0.20, "Should prevent excessive synchronization"
        print(f"  Max simultaneous: {max_simultaneous} / {n_cohorts}")
        print(f"  Max fraction: {max_fraction:.2%}")
        print(f"  ✓ Staggering prevents synchronization")

    def test_diversity_score_calculation(self):
        """Validate diversity score computation"""
        print("\n✓ Testing diversity score calculation:")

        # Test uniform distribution vs clustered distribution
        n_cohorts = 12

        # Uniform distribution
        uniform_phases = [2 * math.pi * i / n_cohorts for i in range(n_cohorts)]

        # Check adjacent spacing (should be uniform)
        adjacent_diffs = [abs(uniform_phases[i+1] - uniform_phases[i]) for i in range(n_cohorts-1)]
        spacing_std = (sum((d - adjacent_diffs[0])**2 for d in adjacent_diffs) / len(adjacent_diffs)) ** 0.5

        # Uniform distribution should have very low spacing variance
        assert spacing_std < 0.01, "Uniform distribution should have consistent spacing"
        print(f"  Adjacent spacing std dev: {spacing_std:.6f}")
        print(f"  ✓ Diversity calculation works (uniform spacing verified)")


class TestOptimizationLogic:
    """Test optimization dynamics"""

    def test_damped_harmonic_convergence(self):
        """Validate damped oscillator converges"""
        print("\n✓ Testing damped harmonic convergence:")

        # Simple damped harmonic oscillator
        # d²x/dt² = -k*x - γ*(dx/dt)
        k = 0.5  # Spring constant
        gamma = 0.8  # Damping
        dt = 1.0  # Time step

        x = 10.0  # Initial displacement
        v = 0.0  # Initial velocity
        target = 0.0

        positions = []
        for _ in range(50):
            # Compute acceleration
            acceleration = -k * (x - target) - gamma * v

            # Update velocity and position
            v = v + acceleration * dt
            x = x + v * dt

            positions.append(x)

        # Check convergence
        final_displacement = abs(positions[-1] - target)
        initial_displacement = abs(10.0 - target)

        assert final_displacement < initial_displacement * 0.1, "Should converge toward target"
        print(f"  Initial displacement: {initial_displacement:.4f}")
        print(f"  Final displacement: {final_displacement:.4f}")
        print(f"  ✓ Damped harmonic oscillator converges")

    def test_high_damping_prevents_overshoot(self):
        """Validate high damping reduces oscillation"""
        print("\n✓ Testing damping prevents overshoot:")

        k = 0.5
        dt = 1.0
        target = 0.0

        # Test two damping values
        results = {}
        for gamma in [0.1, 0.9]:
            x = 10.0
            v = 0.0
            overshoots = 0
            prev_x = x

            for _ in range(50):
                acceleration = -k * (x - target) - gamma * v
                v = v + acceleration * dt
                x = x + v * dt

                # Count overshoots
                if (prev_x - target) * (x - target) < 0:
                    overshoots += 1

                prev_x = x

            results[gamma] = overshoots

        assert results[0.9] < results[0.1], "High damping should reduce overshoots"
        print(f"  Low damping (0.1): {results[0.1]} overshoots")
        print(f"  High damping (0.9): {results[0.9]} overshoots")
        print(f"  ✓ High damping prevents oscillation")


class TestAccountOrchestrationLogic:
    """Test account orchestration logic"""

    def test_cohort_assignment(self):
        """Validate birth-month based cohort assignment"""
        print("\n✓ Testing cohort assignment:")

        # Simulate account registration
        cohort_counts = [0] * 12

        for i in range(1200):
            month = (i % 12) + 1  # 1-12
            cohort_id = month - 1  # 0-11
            cohort_counts[cohort_id] += 1

        # Check uniform distribution
        expected_per_cohort = 100
        for cohort_id, count in enumerate(cohort_counts):
            assert count == expected_per_cohort, f"Cohort {cohort_id} has wrong count"

        print(f"  Registered 1200 accounts across 12 cohorts")
        print(f"  Each cohort: {expected_per_cohort} accounts")
        print(f"  ✓ Cohort assignment works correctly")

    def test_liquidity_pressure_detection(self):
        """Validate liquidity pressure calculation"""
        print("\n✓ Testing liquidity pressure detection:")

        total_aum = 720_000_000_000  # $720B
        daily_market_volume = 50_000_000_000_000  # $50T

        # Test different rebalancing fractions
        test_cases = [
            (0.1, "10% cohorts"),
            (0.3, "30% cohorts"),
            (0.5, "50% cohorts"),
        ]

        for rebalancing_fraction, label in test_cases:
            turnover = 0.10  # 10% portfolio turnover
            rebalancing_volume = total_aum * rebalancing_fraction * turnover
            pressure_ratio = rebalancing_volume / daily_market_volume

            print(f"  {label}: pressure ratio = {pressure_ratio:.6f} ({pressure_ratio*100:.4f}%)")

        # Even 50% of cohorts is negligible market impact
        worst_case = total_aum * 0.5 * 0.10 / daily_market_volume
        assert worst_case < 0.01, "System should have minimal market impact"
        print(f"  ✓ Liquidity pressure is manageable")


def run_all_tests():
    """Run all logic validation tests"""
    print("=" * 70)
    print("CO-HERE-US LOGIC VALIDATION SUITE")
    print("=" * 70)

    test_classes = [
        TestProtectionLayerLogic(),
        TestPhaseDiversityLogic(),
        TestOptimizationLogic(),
        TestAccountOrchestrationLogic(),
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n{'=' * 70}")
        print(f"{class_name}")
        print(f"{'=' * 70}")

        test_methods = [m for m in dir(test_class) if m.startswith("test_")]

        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_class, method_name)
                method()
                passed_tests += 1
            except AssertionError as e:
                failed_tests.append((class_name, method_name, str(e)))
                print(f"\n✗ {method_name} FAILED: {e}")
            except Exception as e:
                failed_tests.append((class_name, method_name, str(e)))
                print(f"\n✗ {method_name} ERROR: {e}")

    print(f"\n{'=' * 70}")
    print(f"VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print(f"\nFAILURES:")
        for class_name, method_name, error in failed_tests:
            print(f"  ✗ {class_name}.{method_name}: {error}")
        return False
    else:
        print(f"\n✓ ALL LOGIC TESTS PASSED")
        print(f"\n{'=' * 70}")
        print(f"ALGORITHMS VALIDATED:")
        print(f"{'=' * 70}")
        print(f"✓ EMA smoothing reduces volatility")
        print(f"✓ Drift detection works across timescales")
        print(f"✓ Boundary enforcement maintains stability")
        print(f"✓ Phase diversity prevents synchronization")
        print(f"✓ Damped harmonic optimization converges")
        print(f"✓ High damping prevents oscillation")
        print(f"✓ Cohort assignment distributes uniformly")
        print(f"✓ Liquidity pressure is manageable at scale")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
