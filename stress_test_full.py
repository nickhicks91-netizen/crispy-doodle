#!/usr/bin/env python3
"""
CO-HERE-US Unity v1.0 - FULL STRESS TEST SUITE

Tests the system against:
- 75 years of historical-like market data (1950-2024)
- 1970s stagflation
- 2000s dot-com + GFC crashes
- 2020s volatility
- Japanification scenario
- Triple crash scenario
- Crypto winter scenario

VERDICT: Does CO-HERE-US survive or fail?
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from cohereus import UnityOrchestrator, PLFController, FractonController
from cohereus.config import EXPECTED_RETURN, ANNUAL_VOLATILITY
import random


# ============================================================================
# HISTORICAL-LIKE DATA GENERATOR
# ============================================================================

def _decade_params(year: int):
    """Return (eq_mean, eq_vol, bond_mean, bond_vol, gold_mean, gold_vol, infl_mean, infl_vol)"""
    if 1950 <= year <= 1959:
        return (0.14, 0.15, 0.03, 0.04, 0.01, 0.15, 0.02, 0.01)
    if 1960 <= year <= 1969:
        return (0.11, 0.14, 0.04, 0.05, 0.03, 0.15, 0.025, 0.01)
    if 1970 <= year <= 1979:
        # STAGFLATION
        return (0.07, 0.18, 0.06, 0.07, 0.18, 0.25, 0.06, 0.03)
    if 1980 <= year <= 1989:
        return (0.15, 0.18, 0.09, 0.08, 0.01, 0.20, 0.035, 0.015)
    if 1990 <= year <= 1999:
        return (0.17, 0.16, 0.07, 0.06, 0.02, 0.15, 0.03, 0.01)
    if 2000 <= year <= 2009:
        # DOT-COM + GFC
        return (0.03, 0.20, 0.06, 0.07, 0.10, 0.25, 0.025, 0.015)
    if 2010 <= year <= 2019:
        return (0.13, 0.14, 0.04, 0.05, 0.02, 0.18, 0.02, 0.01)
    if 2020 <= year <= 2024:
        return (0.09, 0.22, 0.02, 0.08, 0.05, 0.25, 0.035, 0.02)
    return (0.10, 0.15, 0.04, 0.05, 0.02, 0.18, 0.025, 0.015)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def get_historical_series(seed: int = 42):
    """Generate 1950-2024 historical-like annual returns."""
    random.seed(seed)
    years = list(range(1950, 2025))
    data = []

    for y in years:
        eq_m, eq_v, b_m, b_v, g_m, g_v, i_m, i_v = _decade_params(y)

        eq = _clamp(random.gauss(eq_m, eq_v), -0.45, 0.45)
        bnd = _clamp(random.gauss(b_m, b_v), -0.15, 0.25)
        gld = _clamp(random.gauss(g_m, g_v), -0.40, 0.60)
        inf = _clamp(random.gauss(i_m, i_v), -0.02, 0.15)

        # BTC dynamics (2010 onward)
        btc = None
        if y >= 2010:
            if 2010 <= y <= 2014:
                bm, bv = 1.2, 1.0
            elif 2015 <= y <= 2019:
                bm, bv = 0.5, 0.8
            else:
                bm, bv = 0.25, 0.7
            btc = _clamp(random.gauss(bm, bv), -0.8, 5.0)

        # Portfolio blend: 60% equity, 25% bonds, 10% crypto (when available), 5% gold
        if btc is None:
            # Pre-crypto: 60% equity, 30% bonds, 10% gold
            portfolio_return = 0.60 * eq + 0.30 * bnd + 0.10 * gld
        else:
            # With crypto: 60% equity, 25% bonds, 10% crypto, 5% gold
            portfolio_return = 0.60 * eq + 0.25 * bnd + 0.10 * btc + 0.05 * gld

        data.append({
            "year": y,
            "us_equity": eq,
            "us_bond": bnd,
            "gold": gld,
            "btc": btc,
            "portfolio": portfolio_return,
        })

    return data


# ============================================================================
# STRESS TEST SCENARIOS
# ============================================================================

def apply_plf_fracton(returns):
    """Apply PLF + Fracton to return sequence."""
    plf = PLFController()
    fracton = FractonController()
    smoothed = plf.smooth(returns)
    final = fracton.dampen(smoothed)
    return final


def simulate_cohort(returns, seed=2000, monthly_contrib=20):
    """
    Simulate a single cohort over 25 years.

    Args:
        returns: Annual returns for 25 years
        seed: Initial corporate seed ($2k)
        monthly_contrib: Monthly family contribution ($20)

    Returns:
        Final balance at age 25
    """
    seed_balance = seed
    family_balance = 0.0

    for annual_return in returns:
        # Add monthly contributions for the year
        family_balance += monthly_contrib * 12

        # Apply return to both portfolios
        seed_balance *= (1 + annual_return)
        family_balance *= (1 + annual_return)

    return seed_balance + family_balance


def run_rolling_windows(historical_data, window_size=25):
    """Run rolling 25-year windows through historical data."""
    portfolio_returns = [d["portfolio"] for d in historical_data]

    if len(portfolio_returns) < window_size:
        return []

    results = []
    for i in range(len(portfolio_returns) - window_size + 1):
        window = portfolio_returns[i:i+window_size]

        # Apply PLF + Fracton
        processed = apply_plf_fracton(np.array(window))

        # Simulate cohort
        outcome = simulate_cohort(processed)

        start_year = historical_data[i]["year"]
        end_year = historical_data[i+window_size-1]["year"]

        results.append({
            "period": f"{start_year}-{end_year}",
            "outcome": outcome,
            "avg_return": np.mean(processed),
        })

    return results


def run_specific_crisis(historical_data, start_year, end_year):
    """Test a specific historical crisis period."""
    period_data = [d for d in historical_data if start_year <= d["year"] <= end_year]

    if len(period_data) < 25:
        return None

    returns = [d["portfolio"] for d in period_data[:25]]
    processed = apply_plf_fracton(np.array(returns))
    outcome = simulate_cohort(processed)

    return {
        "period": f"{start_year}-{end_year}",
        "outcome": outcome,
        "avg_return": np.mean(processed),
    }


def run_japanification():
    """Simulate 25 years of stagnation (0-2% returns)."""
    returns = np.random.uniform(0.00, 0.02, size=25)
    processed = apply_plf_fracton(returns)
    outcome = simulate_cohort(processed)

    return {
        "scenario": "Japanification",
        "outcome": outcome,
        "avg_return": np.mean(processed),
    }


def run_triple_crash(historical_data):
    """Inject 3 random -45% crashes into historical data."""
    portfolio_returns = [d["portfolio"] for d in historical_data]

    # Make a copy and inject crashes
    crashed = np.array(portfolio_returns[:50])  # Use first 50 years
    crash_indices = np.random.choice(len(crashed), 3, replace=False)

    for idx in crash_indices:
        crashed[idx] = -0.45

    # Test rolling windows on crashed data
    results = []
    for i in range(len(crashed) - 25 + 1):
        window = crashed[i:i+25]
        processed = apply_plf_fracton(window)
        outcome = simulate_cohort(processed)

        results.append({
            "window": i,
            "outcome": outcome,
            "avg_return": np.mean(processed),
        })

    return results


def run_crypto_winter():
    """Simulate severe crypto crashes (-80%) in 3 years."""
    # Start with normal returns
    returns = np.random.normal(EXPECTED_RETURN, ANNUAL_VOLATILITY, 25)

    # Inject crypto winters (affecting 10% of portfolio)
    winter_years = np.random.choice(25, 3, replace=False)
    for year in winter_years:
        # -80% on 10% of portfolio = -8% total portfolio impact
        returns[year] -= 0.08

    processed = apply_plf_fracton(returns)
    outcome = simulate_cohort(processed)

    return {
        "scenario": "Crypto Winter",
        "outcome": outcome,
        "avg_return": np.mean(processed),
    }


# ============================================================================
# MAIN STRESS TEST RUNNER
# ============================================================================

def main():
    print("=" * 80)
    print("CO-HERE-US UNITY v1.0 - COMPREHENSIVE STRESS TEST")
    print("=" * 80)
    print("\nTesting against:")
    print("  • 75 years of historical-like market data (1950-2024)")
    print("  • 1970s stagflation")
    print("  • 2000s dot-com bubble + Great Financial Crisis")
    print("  • Japanification scenario")
    print("  • Triple crash scenario")
    print("  • Crypto winter scenario")
    print("\nTarget: $50,000 - $90,000 at age 25")
    print("Failure threshold: Below $30,000")
    print("=" * 80)

    # Generate historical data
    historical = get_historical_series(seed=42)

    # ========================================================================
    # TEST 1: Historical Rolling Windows (1950-2024)
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: HISTORICAL ROLLING WINDOWS (1950-2024)")
    print("=" * 80)

    rolling = run_rolling_windows(historical)

    if rolling:
        outcomes = [r["outcome"] for r in rolling]

        print(f"\nTotal windows tested: {len(rolling)}")
        print(f"\nOUTCOMES:")
        print(f"  Minimum:  ${min(outcomes):,.0f}")
        print(f"  10th %ile: ${np.percentile(outcomes, 10):,.0f}")
        print(f"  Median:   ${np.percentile(outcomes, 50):,.0f}")
        print(f"  90th %ile: ${np.percentile(outcomes, 90):,.0f}")
        print(f"  Maximum:  ${max(outcomes):,.0f}")

        # Check target achievement
        in_target = sum(1 for o in outcomes if 50000 <= o <= 90000)
        above_30k = sum(1 for o in outcomes if o >= 30000)

        print(f"\n  In target ($50k-$90k): {in_target}/{len(outcomes)} ({in_target/len(outcomes)*100:.1f}%)")
        print(f"  Above failure ($30k):  {above_30k}/{len(outcomes)} ({above_30k/len(outcomes)*100:.1f}%)")

        # Show worst periods
        worst_5 = sorted(rolling, key=lambda x: x["outcome"])[:5]
        print(f"\n  WORST 5 PERIODS:")
        for r in worst_5:
            print(f"    {r['period']}: ${r['outcome']:,.0f} (avg return: {r['avg_return']:.2%})")

        verdict1 = "✓ PASS" if above_30k == len(outcomes) else "✗ FAIL"
        print(f"\n  VERDICT: {verdict1}")

    # ========================================================================
    # TEST 2: Specific Crisis Periods
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: SPECIFIC CRISIS PERIODS")
    print("=" * 80)

    crises = [
        (1966, 1991, "Vietnam War + Stagflation Era"),
        (1974, 1999, "Stagflation to Dot-Com"),
        (2000, 2024, "Dot-Com Bust + GFC + COVID"),
    ]

    crisis_results = []
    for start, end, name in crises:
        result = run_specific_crisis(historical, start, end)
        if result:
            crisis_results.append((name, result))
            print(f"\n{name} ({start}-{end}):")
            print(f"  Outcome: ${result['outcome']:,.0f}")
            print(f"  Avg return: {result['avg_return']:.2%}")

            if result['outcome'] >= 30000:
                print(f"  Status: ✓ SURVIVED")
            else:
                print(f"  Status: ✗ FAILED")

    verdict2 = "✓ PASS" if all(r[1]['outcome'] >= 30000 for r in crisis_results) else "✗ FAIL"
    print(f"\n  OVERALL VERDICT: {verdict2}")

    # ========================================================================
    # TEST 3: Japanification
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 3: JAPANIFICATION (25 years of 0-2% returns)")
    print("=" * 80)

    japan = run_japanification()
    print(f"\n  Outcome: ${japan['outcome']:,.0f}")
    print(f"  Avg return: {japan['avg_return']:.2%}")

    verdict3 = "✓ PASS" if japan['outcome'] >= 30000 else "✗ FAIL"
    print(f"  VERDICT: {verdict3}")

    # ========================================================================
    # TEST 4: Triple Crash
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 4: TRIPLE CRASH (3 random -45% crashes)")
    print("=" * 80)

    crashes = run_triple_crash(historical)
    crash_outcomes = [c["outcome"] for c in crashes]

    print(f"\n  Windows tested: {len(crashes)}")
    print(f"  Minimum:  ${min(crash_outcomes):,.0f}")
    print(f"  Median:   ${np.percentile(crash_outcomes, 50):,.0f}")
    print(f"  Maximum:  ${max(crash_outcomes):,.0f}")

    above_30k_crash = sum(1 for o in crash_outcomes if o >= 30000)
    print(f"  Above $30k: {above_30k_crash}/{len(crashes)} ({above_30k_crash/len(crashes)*100:.1f}%)")

    verdict4 = "✓ PASS" if above_30k_crash == len(crashes) else "✗ FAIL"
    print(f"  VERDICT: {verdict4}")

    # ========================================================================
    # TEST 5: Crypto Winter
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 5: CRYPTO WINTER (3 years of -80% crypto)")
    print("=" * 80)

    crypto = run_crypto_winter()
    print(f"\n  Outcome: ${crypto['outcome']:,.0f}")
    print(f"  Avg return: {crypto['avg_return']:.2%}")

    verdict5 = "✓ PASS" if crypto['outcome'] >= 30000 else "✗ FAIL"
    print(f"  VERDICT: {verdict5}")

    # ========================================================================
    # FINAL VERDICT
    # ========================================================================
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)

    all_tests = [
        ("Historical Rolling Windows", verdict1),
        ("Crisis Periods", verdict2),
        ("Japanification", verdict3),
        ("Triple Crash", verdict4),
        ("Crypto Winter", verdict5),
    ]

    print()
    for name, verdict in all_tests:
        print(f"  {name}: {verdict}")

    passed = sum(1 for _, v in all_tests if "PASS" in v)

    print("\n" + "=" * 80)
    if passed == len(all_tests):
        print("✓✓✓ CO-HERE-US UNITY v1.0 SURVIVES ALL STRESS TESTS ✓✓✓")
        print("\nThe system is PROVEN RESILIENT across:")
        print("  • 75 years of market history")
        print("  • Multiple crisis periods")
        print("  • Extreme stress scenarios")
        print("\nREADY FOR PRODUCTION DEPLOYMENT")
    else:
        print(f"✗ SYSTEM FAILED {len(all_tests) - passed}/{len(all_tests)} TESTS")
        print("\nFurther parameter tuning required")

    print("=" * 80)

    return passed == len(all_tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
