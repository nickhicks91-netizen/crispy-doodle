#!/usr/bin/env python3
"""
Quick validation of CO-HERE-US Unity v1.0 build.

Tests that all components integrate correctly and produce expected outcomes.
"""

import sys
sys.path.insert(0, 'src')

from cohereus import UnityOrchestrator

def main():
    print("CO-HERE-US Unity v1.0 - Build Validation")
    print("=" * 70)

    # Create orchestrator
    orchestrator = UnityOrchestrator(
        births_per_year=3_600_000,
        cohort_duration=25,
        random_seed=42,
    )

    print("\n✓ Orchestrator initialized")
    print(f"  Expected steady state: {orchestrator.get_steady_state_capacity():,} users")

    # Run 50-year simulation
    print("\n⏳ Running 50-year simulation...")
    results = orchestrator.run_simulation(n_years=50)

    print(f"\n✓ Simulation complete")
    print(f"  Years simulated: {results['years_simulated']}")
    print(f"  Active cohorts: {results['active_cohorts']}")
    print(f"  Distributed cohorts: {results['distributed_cohorts']}")
    print(f"  Active children: {results['active_children']:,}")

    # Check outcomes
    if results['distributed_cohorts'] > 0:
        seed_only = results['outcomes']['seed_only']
        seed_family = results['outcomes']['seed_family']

        print("\n" + "=" * 70)
        print("OUTCOMES")
        print("=" * 70)

        print("\nSCENARIO 1: SEED ONLY ($2,000 corporate)")
        print(f"  Average: ${seed_only['mean']:,.0f}")
        print(f"  Range: ${seed_only['min']:,.0f} - ${seed_only['max']:,.0f}")
        print(f"  Std Dev: ${seed_only['std']:,.0f}")

        print("\nSCENARIO 2: SEED + FAMILY ($2,000 + $20/mo)")
        print(f"  Average: ${seed_family['mean']:,.0f}")
        print(f"  Range: ${seed_family['min']:,.0f} - ${seed_family['max']:,.0f}")
        print(f"  Std Dev: ${seed_family['std']:,.0f}")

        # Validate targets
        target_min = 50_000
        target_max = 90_000

        print("\n" + "=" * 70)
        print("VALIDATION")
        print("=" * 70)

        in_target = target_min <= seed_family['mean'] <= target_max
        status = "✓ PASS" if in_target else "✗ FAIL"

        print(f"\nTarget: ${target_min:,} - ${target_max:,}")
        print(f"Actual: ${seed_family['mean']:,.0f}")
        print(f"Status: {status}")

        # Check fairness (low variance)
        variance_pct = (seed_family['std'] / seed_family['mean']) * 100
        fairness = "✓ EXCELLENT" if variance_pct < 1.0 else "⚠ REVIEW"

        print(f"\nInter-cohort variance: {variance_pct:.2f}%")
        print(f"Fairness: {fairness}")

        print("\n" + "=" * 70)

        return 0 if in_target else 1
    else:
        print("\n⚠ No cohorts distributed yet (simulation too short)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
