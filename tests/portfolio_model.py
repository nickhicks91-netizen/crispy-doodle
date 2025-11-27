"""
CO-HERE-US Portfolio Model
Full portfolio logic with adaptive crypto weighting
"""

import numpy as np

class CohereusPortfolio:
    def __init__(self, data):
        self.data = data
        self.crypto_weight_base = 0.10
        self.crypto_max = 0.15
        self.crypto_min = 0.05

    def compute_annual_returns(self):
        """Compute portfolio annual returns with adaptive crypto weighting."""
        print("Computing portfolio annual returns...")

        # Resample monthly to annual
        us = (1 + self.data.us_equities).resample("YE").prod() - 1
        gl = (1 + self.data.global_equities).resample("YE").prod() - 1
        ts = (1 + self.data.treasuries).resample("YE").prod() - 1
        cr = (1 + self.data.crypto).resample("YE").prod() - 1

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

            # Adaptive crypto weighting - look at previous 3 years
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

        return annual_portfolio, years
