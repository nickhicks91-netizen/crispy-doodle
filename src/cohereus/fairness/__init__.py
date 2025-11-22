"""
CO-HERE-US Fairness Layer

Core fairness guarantees:
- Contribution caps ($20/mo maximum)
- Automatic refunds for overages

DNA Source: Economic justice principles
"""

from .contribution_cap import ContributionCap, CapConfig

__all__ = [
    "ContributionCap",
    "CapConfig",
]
