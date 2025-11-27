"""
CO-HERE-US Stress Tests
All scenarios: historical, worst windows, Japanification, triple crash, crypto winter
"""

import numpy as np

class StressTester:
    def __init__(self, system):
        self.system = system

    def run_all(self):
        """Run all stress tests."""
        print("Running all stress tests...\n")

        results = {}

        # 1. Historical rolling windows
        ann, years = self.system.portfolio.compute_annual_returns()
        results["historical"] = self.system.simulate_all_windows(ann)

        # 2. Specific worst windows
        ann_array = np.array(ann)

        # Find indices for specific periods
        year_list = [y.year for y in years]

        try:
            idx_1966 = year_list.index(1966)
            idx_1991 = year_list.index(1991)
            if idx_1991 - idx_1966 >= 25:
                results["1966_1991"] = self.system.simulate_25_year_window(
                    ann_array[idx_1966:idx_1966+25]
                )
        except (ValueError, IndexError):
            pass

        try:
            idx_1974 = year_list.index(1974)
            idx_1999 = year_list.index(1999)
            if idx_1999 - idx_1974 >= 25:
                results["1974_1999"] = self.system.simulate_25_year_window(
                    ann_array[idx_1974:idx_1974+25]
                )
        except (ValueError, IndexError):
            pass

        try:
            idx_2000 = year_list.index(2000)
            if len(ann_array) - idx_2000 >= 25:
                results["2000_2025"] = self.system.simulate_25_year_window(
                    ann_array[idx_2000:idx_2000+25]
                )
            else:
                # Use last 25 years
                results["2000_2025"] = self.system.simulate_25_year_window(
                    ann_array[-25:]
                )
        except (ValueError, IndexError):
            pass

        # 3. Japanification (0-2% real returns for 25 years)
        japan = np.random.uniform(0.00, 0.02, size=25)
        results["japanification"] = self.system.simulate_25_year_window(japan)

        # 4. Triple crash (-45% in 3 random years)
        crash = ann_array.copy()
        if len(crash) > 25:
            shock_years = np.random.choice(min(len(crash), 50), 3, replace=False)
            for y in shock_years:
                crash[y] -= 0.45
            results["triple_crash"] = self.system.simulate_all_windows(crash)

        # 5. Crypto winter (-80% crypto, affects ~10% of portfolio = -8% total)
        cw = ann_array.copy()
        if len(cw) > 25:
            winter_years = np.random.choice(min(len(cw), 50), 3, replace=False)
            for y in winter_years:
                cw[y] -= 0.08  # -80% on 10% of portfolio
            results["crypto_winter"] = self.system.simulate_all_windows(cw)

        return results
