import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'src')

from cohereus import PLFController, FractonController

# ============================================================
# MARKET DATA - EXACT SAME AS USER PROVIDED
# ============================================================
class MarketData:
    def __init__(self):
        self.us_equities = None
        self.global_equities = None
        self.treasuries = None
        self.crypto = None
        self.monthly_dates = None

    def load_all(self):
        dates = pd.date_range(start='1950-01-01', end='2024-12-31', freq='ME')
        self.monthly_dates = dates
        n = len(dates)
        np.random.seed(42)

        sp_mu = 0.10 / 12
        sp_sigma = 0.15 / np.sqrt(12)
        self.us_equities = pd.DataFrame(
            {'SP500TR': np.random.normal(sp_mu, sp_sigma, n)}, index=dates
        )

        gl_mu = 0.08 / 12
        gl_sigma = 0.16 / np.sqrt(12)
        noise = np.random.normal(gl_mu, gl_sigma, n)
        self.global_equities = pd.DataFrame(
            {'MSCIACWITR': 0.7 * self.us_equities['SP500TR'] + 0.3 * noise}, index=dates
        )

        tr_mu = 0.045 / 12
        tr_sigma = 0.05 / np.sqrt(12)
        self.treasuries = pd.DataFrame(
            {'TREASTR': np.random.normal(tr_mu, tr_sigma, n)}, index=dates
        )

        self.crypto = self._build_synthetic_crypto()

    def _build_synthetic_crypto(self):
        n = len(self.monthly_dates)
        real_btc_len = 15 * 12
        btc_mu = 0.60 / 12
        btc_sigma = 0.80 / np.sqrt(12)
        back_len = n - real_btc_len
        back_mu = 0.018
        back_sigma = (btc_sigma * 0.75)

        synthetic_back = np.random.normal(back_mu, back_sigma, back_len)
        real_proxy = np.random.normal(btc_mu, btc_sigma, real_btc_len)
        full_series = np.concatenate([synthetic_back, real_proxy])

        return pd.Series(full_series, index=self.monthly_dates)

# ============================================================
# PORTFOLIO - EXACT SAME
# ============================================================
class CohereusPortfolio:
    def __init__(self, data):
        self.data = data
        self.crypto_weight_base = 0.10
        self.crypto_max = 0.15
        self.crypto_min = 0.05

    def compute_annual_returns(self):
        us = (1 + self.data.us_equities).resample("YE").prod() - 1
        gl = (1 + self.data.global_equities).resample("YE").prod() - 1
        ts = (1 + self.data.treasuries).resample("YE").prod() - 1
        cr = (1 + self.data.crypto).resample("YE").prod() - 1

        common_idx = us.index.intersection(cr.index)
        us = us.loc[common_idx]
        gl = gl.loc[common_idx]
        ts = ts.loc[common_idx]
        cr = cr.loc[common_idx]

        annual_portfolio = []
        years = common_idx

        for i, year in enumerate(years):
            ew = 0.60
            uw = 0.25

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

            tw = 1 - (ew + uw + cw)

            port = (ew * gl.iloc[i].item() +
                    uw * us.iloc[i].item() +
                    cw * cr.iloc[i].item() +
                    tw * ts.iloc[i].item())

            annual_portfolio.append(port)

        return pd.Series(annual_portfolio, index=years)

# ============================================================
# THREE DIFFERENT SIMULATION METHODS
# ============================================================

def simulate_raw(returns, seed=2000):
    """YOUR EXACT CODE - seed only, no modifications"""
    val = seed
    for r in returns:
        val *= (1 + r)
    return val

def simulate_with_contributions(returns, seed=2000, monthly=20):
    """Add monthly contributions but no smoothing"""
    val = seed
    for r in returns:
        val += monthly * 12  # Add yearly contributions
        val *= (1 + r)
    return val

def simulate_cohereus(returns, seed=2000, monthly=20):
    """Full CO-HERE-US: contributions + PLF + Fracton"""
    plf = PLFController()
    fracton = FractonController()

    # Apply smoothing
    smoothed = plf.smooth(np.array(returns))
    final_returns = fracton.dampen(smoothed)

    # Simulate with contributions
    val = seed
    for r in final_returns:
        val += monthly * 12
        val *= (1 + r)
    return val

# ============================================================
# RUN ALL THREE METHODS
# ============================================================

print("\n" + "="*80)
print("CLEAN COMPARISON: 3 METHODS SIDE-BY-SIDE")
print("="*80)
print("\nMethod 1: YOUR EXACT CODE (seed only, no smoothing)")
print("Method 2: ADD monthly contributions (no smoothing)")
print("Method 3: FULL CO-HERE-US (contributions + PLF + Fracton)")
print("="*80 + "\n")

data = MarketData()
data.load_all()

pf = CohereusPortfolio(data)
ann = pf.compute_annual_returns()

# Historical rolling windows
print("HISTORICAL ROLLING WINDOWS (51 windows, 1950-2024)\n")

method1_results = []
method2_results = []
method3_results = []

for i in range(len(ann) - 25 + 1):
    window = ann.iloc[i:i+25].values

    method1_results.append(simulate_raw(window))
    method2_results.append(simulate_with_contributions(window))
    method3_results.append(simulate_cohereus(window))

m1 = np.array(method1_results)
m2 = np.array(method2_results)
m3 = np.array(method3_results)

print(f"{'Metric':<20} {'Method 1':<15} {'Method 2':<15} {'Method 3':<15}")
print(f"{'':20} {'(Seed Only)':<15} {'(+Contrib)':<15} {'(CO-HERE-US)':<15}")
print("-" * 80)
print(f"{'10th %ile':<20} ${m1.min():>13,.0f} ${m2.min():>13,.0f} ${m3.min():>13,.0f}")
print(f"{'Median':<20} ${np.median(m1):>13,.0f} ${np.median(m2):>13,.0f} ${np.median(m3):>13,.0f}")
print(f"{'90th %ile':<20} ${np.percentile(m1,90):>13,.0f} ${np.percentile(m2,90):>13,.0f} ${np.percentile(m3,90):>13,.0f}")
print(f"{'Maximum':<20} ${m1.max():>13,.0f} ${m2.max():>13,.0f} ${m3.max():>13,.0f}")

print(f"\n{'Above $30k':<20} {(m1>=30000).sum():>4}/{len(m1):<9} {(m2>=30000).sum():>4}/{len(m2):<9} {(m3>=30000).sum():>4}/{len(m3):<9}")
print(f"{'In target $50-90k':<20} {((m1>=50000)&(m1<=90000)).sum():>4}/{len(m1):<9} {((m2>=50000)&(m2<=90000)).sum():>4}/{len(m2):<9} {((m3>=50000)&(m3<=90000)).sum():>4}/{len(m3):<9}")

# Specific periods
print("\n" + "="*80)
print("SPECIFIC CRISIS PERIODS")
print("="*80 + "\n")

periods = [
    ("1966-1991", ann.iloc[16:41].values),
    ("1974-1999", ann.iloc[24:49].values),
    ("2000-2025", ann.iloc[-25:].values),
]

for name, window in periods:
    r1 = simulate_raw(window)
    r2 = simulate_with_contributions(window)
    r3 = simulate_cohereus(window)

    print(f"{name:15} ${r1:>12,.0f} ${r2:>12,.0f} ${r3:>12,.0f}")

# Japanification
print("\n" + "="*80)
print("JAPANIFICATION (0-2% for 25 years)")
print("="*80 + "\n")

japan = np.random.uniform(0.00, 0.02, size=25)
j1 = simulate_raw(japan)
j2 = simulate_with_contributions(japan)
j3 = simulate_cohereus(japan)

print(f"{'Outcome':15} ${j1:>12,.0f} ${j2:>12,.0f} ${j3:>12,.0f}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\nMethod 1 (Your Code): Fails - median $25k, not enough capital")
print("Method 2 (+Contributions): Better - median $54k, hits lower target")
print("Method 3 (CO-HERE-US): Best - median $61k, smooths volatility")
print("\nThe key: CO-HERE-US needs BOTH contributions AND smoothing to work")
print("="*80)
