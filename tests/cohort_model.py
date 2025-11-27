"""
CO-HERE-US Cohort Model
Simulates all 24 overlapping 25-year cohorts (90M accounts)
"""

import sys
sys.path.insert(0, '../src')

import numpy as np
from cohereus import PLFController, FractonController

class CohortSystem:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.seed = 2000
        self.monthly_contrib = 20
        self.kids_per_year = 3_600_000
        self.plf = PLFController()
        self.fracton = FractonController()

    def simulate_25_year_window(self, returns):
        """Simulate a single 25-year cohort with PLF + Fracton."""
        # Apply PLF smoothing
        returns_array = np.array(returns)
        smoothed = self.plf.smooth(returns_array)

        # Apply Fracton dampening
        final_returns = self.fracton.dampen(smoothed)

        # Simulate growth with seed + monthly contributions
        seed_balance = self.seed
        family_balance = 0.0

        for r in final_returns:
            # Add monthly contributions
            family_balance += self.monthly_contrib * 12

            # Apply return
            seed_balance *= (1 + r)
            family_balance *= (1 + r)

        return seed_balance + family_balance

    def simulate_all_windows(self, annual_returns):
        """Simulate all rolling 25-year windows."""
        results = []
        arr = np.array(annual_returns)

        if len(arr) < 25:
            return np.array([])

        for i in range(len(arr) - 25 + 1):
            window = arr[i:i+25]
            final = self.simulate_25_year_window(window)
            results.append(final)

        return np.array(results)
