"""
CO-HERE-US Data Loader
Loads historical market data with synthetic crypto backfill
"""

import pandas as pd
import numpy as np

class MarketData:
    def __init__(self):
        self.us_equities = None
        self.global_equities = None
        self.treasuries = None
        self.crypto = None
        self.monthly_dates = None

    def load_all(self):
        """Load all historical datasets."""
        print("Loading historical datasets...")

        # Generate Monthly Dates (1950 to 2024)
        dates = pd.date_range(start='1950-01-01', end='2024-12-31', freq='ME')
        self.monthly_dates = dates
        n = len(dates)
        np.random.seed(42)

        # --- GENERATE STATISTICAL PROXIES FOR HISTORICAL DATA ---
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
            {'MSCIACWITR': 0.7 * self.us_equities['SP500TR'] + 0.3 * noise},
            index=dates
        )

        # Treasuries (Approx 4.5% annual, 5% vol)
        tr_mu = 0.045 / 12
        tr_sigma = 0.05 / np.sqrt(12)
        self.treasuries = pd.DataFrame(
            {'TREASTR': np.random.normal(tr_mu, tr_sigma, n)}, index=dates
        )

        # Build Crypto with synthetic backfill
        self.crypto = self._build_synthetic_crypto()

        print("Data loading complete.\n")

    def _build_synthetic_crypto(self):
        """Build crypto series with pre-2010 synthetic backfill."""
        print("Building synthetic crypto series (1950–2009 backfill)...")

        n = len(self.monthly_dates)

        # Real BTC proxy (2010-2024) - High Vol, High Return
        real_btc_len = 15 * 12  # 180 months
        btc_mu = 0.60 / 12  # Aggressive annual growth
        btc_sigma = 0.80 / np.sqrt(12)

        # Synthetic Backfill (1950-2009)
        back_len = n - real_btc_len
        back_mu = 0.018  # ~22%/yr
        back_sigma = btc_sigma * 0.75  # Dampened vol

        synthetic_back = np.random.normal(back_mu, back_sigma, back_len)
        real_proxy = np.random.normal(btc_mu, btc_sigma, real_btc_len)

        full_series = np.concatenate([synthetic_back, real_proxy])

        return pd.Series(full_series, index=self.monthly_dates)
