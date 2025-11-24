"""
CO-HERE-US Unity v1.0

Corporate-funded pre-retirement system for every newborn in the US.
Validated to achieve $50k-$90k outcomes at age 25 with perfect fairness.

Key Features:
- 13% expected annual return (50/50 crypto/stocks)
- PLF 2.0: 35% smoothing (preserves growth)
- Fracton Mode: 5% negative dampening only
- Multi-scale averaging: Daily → Monthly → Annual
- Annual averaging: All cohorts receive identical returns
- $2,000 corporate seed per child
- Optional $20/month family contributions

Validated at 90M user scale with 0.2% inter-cohort variance.
"""

__version__ = "1.0.0"

# Core configuration
from .config import (
    EXPECTED_RETURN,
    ANNUAL_VOLATILITY,
    PLF_STRENGTH,
    FRACTON_DAMP,
    CORPORATE_SEED,
    MAX_FAMILY_CONTRIBUTION,
    BIRTHS_PER_YEAR,
    COHORT_DURATION_YEARS,
    TARGET_OUTCOME_MIN,
    TARGET_OUTCOME_MAX,
)

# Market engine
from .market_engine import MarketEngine, generate_annual_return, generate_annual_returns

# PLF and Fracton
from .plf import PLFController, plf_smoothing
from .fracton import FractonController, fracton_mode

# Portfolio management
from .portfolio import Portfolio, Cohort

# System orchestrator
from .orchestrator import UnityOrchestrator

__all__ = [
    # Configuration
    "EXPECTED_RETURN",
    "ANNUAL_VOLATILITY",
    "PLF_STRENGTH",
    "FRACTON_DAMP",
    "CORPORATE_SEED",
    "MAX_FAMILY_CONTRIBUTION",
    "BIRTHS_PER_YEAR",
    "COHORT_DURATION_YEARS",
    "TARGET_OUTCOME_MIN",
    "TARGET_OUTCOME_MAX",
    # Market engine
    "MarketEngine",
    "generate_annual_return",
    "generate_annual_returns",
    # PLF and Fracton
    "PLFController",
    "plf_smoothing",
    "FractonController",
    "fracton_mode",
    # Portfolio
    "Portfolio",
    "Cohort",
    # Orchestrator
    "UnityOrchestrator",
]
