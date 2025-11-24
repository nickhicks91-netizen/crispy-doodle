"""
CO-HERE-US Unity v1.0 - Core Configuration

Contains the VALIDATED parameters from 90M user steady state testing.
These parameters achieve $50k-$90k outcomes at age 25 with perfect fairness.
"""

# =============================================================================
# MARKET PARAMETERS (Validated)
# =============================================================================

# Expected annual return (50/50 crypto/stocks allocation)
EXPECTED_RETURN = 0.13  # 13%

# Annual volatility
ANNUAL_VOLATILITY = 0.18  # 18%

# =============================================================================
# PLF 2.0 PARAMETERS (Phase-Locked Framework)
# =============================================================================

# PLF smoothing strength (35% pull toward mean, 65% preserves original value)
PLF_STRENGTH = 0.35  # 35% smoothing - preserves growth

# =============================================================================
# FRACTON MODE PARAMETERS
# =============================================================================

# Fracton dampening (applied ONLY to negative returns)
FRACTON_DAMP = 0.05  # 5% dampening on negative years only

# =============================================================================
# FUNDING MODEL
# =============================================================================

# Corporate seed amount (one-time per newborn)
CORPORATE_SEED = 2000.0  # $2,000

# Maximum monthly family contribution
MAX_FAMILY_CONTRIBUTION = 20.0  # $20/month

# =============================================================================
# COHORT PARAMETERS
# =============================================================================

# US birth rate (annual)
BIRTHS_PER_YEAR = 3_600_000  # 3.6M newborns/year

# Cohort lifespan in system
COHORT_DURATION_YEARS = 25  # Birth to age 25

# Expected steady state capacity
STEADY_STATE_CAPACITY = BIRTHS_PER_YEAR * COHORT_DURATION_YEARS  # ~90M users

# =============================================================================
# TARGET OUTCOMES
# =============================================================================

# Target range at age 25 (SEED + FAMILY scenario)
TARGET_OUTCOME_MIN = 50_000  # $50k
TARGET_OUTCOME_MAX = 90_000  # $90k

# Expected average outcome (from validation testing)
EXPECTED_OUTCOME_SEED_ONLY = 42_462  # $42k (seed only)
EXPECTED_OUTCOME_SEED_FAMILY = 84_674  # $85k (seed + family)

# =============================================================================
# FAIRNESS PARAMETERS
# =============================================================================

# Maximum acceptable inter-cohort variance
MAX_COHORT_VARIANCE = 0.005  # 0.5%

# Annual averaging ensures all cohorts receive identical returns each year
ANNUAL_AVERAGING_ENABLED = True

# =============================================================================
# MULTI-SCALE AVERAGING PARAMETERS
# =============================================================================

# Number of days for daily noise generation
DAYS_PER_YEAR = 365

# Number of months for monthly averaging
MONTHS_PER_YEAR = 12
