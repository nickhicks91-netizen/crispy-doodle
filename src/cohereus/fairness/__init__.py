"""
CO-HERE-US Fairness Layer

Core fairness guarantees:
- Contribution caps ($20/mo maximum)
- Cohort equalization (equal outcomes targeting)
- Quarterly rebalancing schedule
- Anti-discrimination safeguards

DNA Source: Economic justice principles
"""

from .contribution_cap import ContributionCap, CapConfig
from .cohort_equalizer import CohortEqualizer, EqualizationConfig
from .fairness_policy import FairnessPolicy, FairnessMetrics

__all__ = [
    "ContributionCap",
    "CapConfig",
    "CohortEqualizer",
    "EqualizationConfig",
    "FairnessPolicy",
    "FairnessMetrics",
]
