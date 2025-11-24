"""
CO-HERE-US Unity v1.0 - Market Engine

Implements multi-scale averaging for return generation.
Daily → Monthly → Annual averaging smooths volatility while preserving expected returns.
"""

import numpy as np
from typing import List

from .config import (
    EXPECTED_RETURN,
    ANNUAL_VOLATILITY,
    DAYS_PER_YEAR,
    MONTHS_PER_YEAR,
)


def generate_annual_return() -> float:
    """
    Multi-Scale Averaging (Daily → Monthly → Annual).

    Generates one year's return using proper multi-scale averaging.
    This naturally smooths volatility while preserving the expected mean.

    Process:
    1. Generate 365 days of noise (mean=0, scaled volatility)
    2. Average to 12 monthly values (reduces volatility)
    3. Average to 1 annual value (further reduces volatility)
    4. Add expected return to smoothed noise

    Returns:
        float: Annual return (e.g., 0.13 for 13%)
    """
    # Generate daily noise (mean=0, volatility based on daily variance)
    daily_noise = np.random.normal(0, ANNUAL_VOLATILITY / np.sqrt(DAYS_PER_YEAR), DAYS_PER_YEAR)

    # Average to monthly (reduces volatility)
    monthly_chunks = np.array_split(daily_noise, MONTHS_PER_YEAR)
    monthly_noise = np.array([chunk.mean() for chunk in monthly_chunks])

    # Average to annual (further reduces volatility)
    annual_noise = monthly_noise.mean()

    # Add expected return to the smoothed noise
    annual_return = EXPECTED_RETURN + annual_noise

    return annual_return


def generate_annual_returns(n_years: int) -> np.ndarray:
    """
    Generate multiple years of returns using multi-scale averaging.

    Args:
        n_years: Number of years to generate

    Returns:
        np.ndarray: Array of annual returns
    """
    return np.array([generate_annual_return() for _ in range(n_years)])


class MarketEngine:
    """
    Market return generator with multi-scale averaging.

    This class provides a clean interface for generating market returns
    that will be processed by PLF and Fracton layers.
    """

    def __init__(self, seed: int = None):
        """
        Initialize market engine.

        Args:
            seed: Random seed for reproducibility (optional)
        """
        if seed is not None:
            np.random.seed(seed)

    def generate_year(self) -> float:
        """
        Generate a single year's return.

        Returns:
            float: Annual return
        """
        return generate_annual_return()

    def generate_sequence(self, n_years: int) -> List[float]:
        """
        Generate a sequence of annual returns.

        Args:
            n_years: Number of years to generate

        Returns:
            List[float]: List of annual returns
        """
        return generate_annual_returns(n_years).tolist()

    def get_expected_return(self) -> float:
        """Get the expected annual return."""
        return EXPECTED_RETURN

    def get_volatility(self) -> float:
        """Get the annual volatility."""
        return ANNUAL_VOLATILITY
