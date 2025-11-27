#!/usr/bin/env python3
"""
CO-HERE-US NATIONAL STRESS TEST SUITE — MASTER RUNNER
Real Data • National Scale • Crypto Synthetic Backfill
"""

from data_loader import MarketData
from portfolio_model import CohereusPortfolio
from cohort_model import CohortSystem
from stress_tests import StressTester
from report_gen import ReportGenerator

def main():
    print("\n" + "=" * 80)
    print("CO-HERE-US VALIDATION SUITE (NATIONAL SCALE)")
    print("=" * 80)
    print("\nSimulating:")
    print("  • 3.6M newborns per year")
    print("  • 90M users at steady state (24 overlapping cohorts)")
    print("  • $2,000 corporate seed + $20/month family contributions")
    print("  • 75 years of historical market data (1950-2024)")
    print("  • PLF 2.0 smoothing (35%) + Fracton dampening (5%)")
    print("  • Adaptive crypto weighting (10% base, 5-15% range)")
    print("=" * 80)
    print()

    # 1. Load all historical data
    data = MarketData()
    data.load_all()

    # 2. Build the portfolio model
    pf = CohereusPortfolio(data)

    # 3. Build the cohort system
    system = CohortSystem(pf)

    # 4. Run all stress tests
    tester = StressTester(system)
    results = tester.run_all()

    # 5. Generate final report
    report = ReportGenerator(results)
    stats = report.generate()

    print("\n" + "=" * 80)
    print("COMPLETE — NATIONAL-SCALE VALIDATION FINISHED")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
