#!/usr/bin/env python3
"""
CO-HERE-US Stress Test - EXACT IMPLEMENTATION from user's spec

Uses the FULL test suite with:
- Monthly data resampled to annual
- Adaptive crypto weighting (10% base, 5-15% range)
- All original test scenarios
"""

import sys
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
from cohereus import PLFController, FractonController

# ============================================================
#  MarketData - EXACT from user spec
# ============================================================
class MarketData:
    def __init__(self):
        self.us_equities = None
        self.global_equities = None
        self.treasuries = None
        self.crypto = None
        self.monthly_dates = None

    def load_all(self):
        # Generate Monthly Dates (1950 to 2024)
        dates = pd.date_range(start='1950-01-01', end='2024-12-31', freq='M')
        self.monthly_dates = dates
        n = len(dates)
        np.random.seed(42)

        # S&P 500 (Approx 10% annual, 15% vol)
        sp_mu = 0.10 / 12
        sp_sigma = 0.15 / np.sqrt(12)
        self.us_equities = pd.DataFrame(
            {'SP500TR': np.random.normal(sp_mu, sp_sigma, n)}, index=dates
        )

        # MSCI World (Approx 8% annual, 16% vol) - correlated with US
        gl_mu = 0.08 / 12
        gl_sigma = 0.16 / np.sqrt(12)
        noise = np.random.normal(gl_mu, gl_sigma, n)
        self.global_equities = pd.DataFrame(
            {'MSCIACWITR': 0.7 * self.us_equities['SP500TR'] + 0.3 * noise}, index=dates
        )

        # Treasuries (Approx 4.5% annual, 5% vol)
        tr_mu = 0.045 / 12
        tr_sigma = 0.05 / np.sqrt(12)
        self.treasuries = pd.DataFrame(
            {'TREASTR': np.random.normal(tr_mu, tr_sigma, n)}, index=dates
        )

        # Build Crypto
        self.crypto = self._build_synthetic_crypto()

    def _build_synthetic_crypto(self):
        n = len(self.monthly_dates)

        # Real BTC proxy (2010-2024)
        real_btc_len = 15 * 12
        btc_mu = 0.60 / 12
        btc_sigma = 0.80 / np.sqrt(12)

        # Synthetic Backfill (1950-2009)
        back_len = n - real_btc_len
        back_mu = 0.018
        back_sigma = (btc_sigma * 0.75)

        synthetic_back = np.random.normal(back_mu, back_sigma, back_len)
        real_proxy = np.random.normal(btc_mu, btc_sigma, real_btc_len)

        full_series = np.concatenate([synthetic_back, real_proxy])

        return pd.Series(full_series, index=self.monthly_dates)


# ============================================================
#  CohereusPortfolio - EXACT from user spec with ADAPTIVE CRYPTO
# ============================================================
class CohereusPortfolio:
    def __init__(self, data):
        self.data = data
        self.crypto_weight_base = 0.10
        self.crypto_max = 0.15
        self.crypto_min = 0.05

    def compute_annual_returns(self):
        # Resample monthly to annual
        us = (1 + self.data.us_equities).resample("Y").prod() - 1
        gl = (1 + self.data.global_equities).resample("Y").prod() - 1
        ts = (1 + self.data.treasuries).resample("Y").prod() - 1
        cr = (1 + self.data.crypto).resample("Y").prod() - 1

        # Align indices
        common_idx = us.index.intersection(cr.index)
        us = us.loc[common_idx]
        gl = gl.loc[common_idx]
        ts = ts.loc[common_idx]
        cr = cr.loc[common_idx]

        annual_portfolio = []
        years = common_idx

        for i, year in enumerate(years):
            ew = 0.60  # Global equity weight
            uw = 0.25  # US equity weight

            # ADAPTIVE crypto weighting - look at previous 3 years
            if i < 3:
                cw = self.crypto_weight_base
            else:
                window = cr.iloc[i-3:i]
                trend = window.mean().item()

                cw = self.crypto_weight_base
                if trend > 0:
                    cw = min(self.crypto_max, cw + 0.05)
                else:
                    cw = max(self.crypto_min, cw - 0.05)

            tw = 1 - (ew + uw + cw)  # Treasury weight (residual)

            # Calculate weighted return
            port = (ew * gl.iloc[i].item() +
                    uw * us.iloc[i].item() +
                    cw * cr.iloc[i].item() +
                    tw * ts.iloc[i].item())

            annual_portfolio.append(port)

        return pd.Series(annual_portfolio, index=years)


# ============================================================
#  CohortSystem - EXACT from user spec
# ============================================================
class CohortSystem:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.seed = 2000
        self.kids_per_year = 3600000

    def simulate_25_year_window(self, returns):
        """Simulate with PLF + Fracton applied."""
        # Apply PLF + Fracton
        plf = PLFController()
        fracton = FractonController()

        returns_array = np.array(returns)
        smoothed = plf.smooth(returns_array)
        final_returns = fracton.dampen(smoothed)

        # Simulate growth
        val = self.seed
        for r in final_returns:
            val += 20 * 12  # Monthly family contributions
            val *= (1 + r)

        return val

    def simulate_all_windows(self, annual_returns):
        results = []
        arr = np.array(annual_returns)

        if len(arr) < 25:
            return np.array([])

        for i in range(len(arr) - 25 + 1):
            window = arr[i:i+25]
            final = self.simulate_25_year_window(window)
            results.append(final)

        return np.array(results)


# ============================================================
#  StressTester - EXACT from user spec
# ============================================================
class StressTester:
    def __init__(self, system):
        self.system = system

    def run_all(self):
        results = {}

        # 1. Historical rolling windows
        ann = self.system.portfolio.compute_annual_returns()
        results["historical"] = self.system.simulate_all_windows(ann)

        # 2. Specific Windows
        if len(ann) > 41:
            results["1966_1991"] = self.system.simulate_25_year_window(ann.iloc[16:41])

        if len(ann) > 49:
            results["1974_1999"] = self.system.simulate_25_year_window(ann.iloc[24:49])

        if len(ann) > 74:
            results["2000_2025"] = self.system.simulate_25_year_window(ann.iloc[50:75])
        else:
            results["2000_2025"] = self.system.simulate_25_year_window(ann.iloc[-25:])

        # 3. Japanification
        japan = np.random.uniform(0.00, 0.02, size=25)
        results["japanification"] = self.system.simulate_25_year_window(japan)

        # 4. Triple Crash
        crash = ann.copy().values
        if len(crash) > 0:
            shock_years = np.random.choice(len(crash), 3, replace=False)
            for y in shock_years:
                crash[y] -= 0.45
            results["triple_crash"] = self.system.simulate_all_windows(crash)

        # 5. Crypto Winter
        cw = ann.copy().values
        if len(cw) > 0:
            winter_years = np.random.choice(len(cw), 3, replace=False)
            for y in winter_years:
                cw[y] -= 0.80
            results["crypto_winter"] = self.system.simulate_all_windows(cw)

        return results


# ============================================================
#  ReportGenerator - EXACT from user spec
# ============================================================
class ReportGenerator:
    def __init__(self, results):
        self.results = results

    def generate(self):
        print("=" * 80)
        print("CO-HERE-US VALIDATION REPORT (EXACT USER SPEC)")
        print("=" * 80)
        print()

        stats = {}

        for name, arr in self.results.items():
            arr = np.array(arr).astype(float)
            if arr.size == 0:
                continue

            if len(arr.shape) == 0:
                arr = np.array([arr])

            p10 = np.percentile(arr, 10)
            med = np.percentile(arr, 50)
            p90 = np.percentile(arr, 90)

            print(f"--- {name.upper()} ---")
            print(f"10th percentile : ${p10:,.0f}")
            print(f"Median          : ${med:,.0f}")
            print(f"90th percentile : ${p90:,.0f}")

            # Additional stats
            if len(arr) > 1:
                print(f"Min             : ${np.min(arr):,.0f}")
                print(f"Max             : ${np.max(arr):,.0f}")
                print(f"Count           : {len(arr)}")

                # Check target achievement
                in_target = np.sum((arr >= 50000) & (arr <= 90000))
                above_30k = np.sum(arr >= 30000)
                print(f"In target ($50k-$90k): {in_target}/{len(arr)} ({in_target/len(arr)*100:.1f}%)")
                print(f"Above failure ($30k):  {above_30k}/{len(arr)} ({above_30k/len(arr)*100:.1f}%)")

            print()

            stats[name] = [p10, med, p90]

        return stats


# ============================================================
#  MASTER EXECUTION - EXACT from user spec
# ============================================================
def main():
    print("=" * 80)
    print("RUNNING EXACT USER-PROVIDED STRESS TEST SUITE")
    print("=" * 80)
    print("\nParameters:")
    print("  • Monthly data (1950-2024) resampled to annual")
    print("  • Adaptive crypto weighting (10% base, 5-15% range)")
    print("  • PLF 2.0: 35% smoothing")
    print("  • Fracton: 5% negative dampening")
    print("  • Seed: $2,000 + $20/month family contributions")
    print("=" * 80)
    print()

    data = MarketData()
    data.load_all()

    pf = CohereusPortfolio(data)
    system = CohortSystem(pf)
    tester = StressTester(system)
    results = tester.run_all()

    report = ReportGenerator(results)
    stats = report.generate()

    # Final verdict
    print("=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)

    # Check key metrics
    hist = results.get("historical", np.array([]))
    if len(hist) > 0:
        hist_above_30k = np.sum(hist >= 30000)
        hist_pct = hist_above_30k / len(hist) * 100

        print(f"\nHistorical rolling windows: {hist_above_30k}/{len(hist)} ({hist_pct:.1f}%) above $30k")

    # Check specific crises
    crisis_pass = 0
    crisis_total = 0
    for crisis in ["1966_1991", "1974_1999", "2000_2025"]:
        if crisis in results:
            crisis_total += 1
            if results[crisis] >= 30000:
                crisis_pass += 1
                print(f"{crisis}: ${results[crisis]:,.0f} ✓ PASS")
            else:
                print(f"{crisis}: ${results[crisis]:,.0f} ✗ FAIL")

    # Check japanification
    japan = results.get("japanification", 0)
    japan_status = "✓ PASS" if japan >= 30000 else "✗ FAIL"
    print(f"Japanification: ${japan:,.0f} {japan_status}")

    print("=" * 80)


if __name__ == "__main__":
    main()
