"""
CO-HERE-US Unity v1.0 - Portfolio Management

Manages individual portfolios with corporate seed and optional family contributions.
"""

from dataclasses import dataclass
from typing import Optional

from .config import CORPORATE_SEED, MAX_FAMILY_CONTRIBUTION


@dataclass
class Portfolio:
    """
    Individual portfolio for one child.

    Tracks:
    - Seed portfolio (from corporate $2k one-time seed)
    - Family portfolio (from optional $20/month contributions)
    """

    seed_balance: float
    family_balance: float
    age_years: int = 0
    months_active: int = 0

    @classmethod
    def create_new(cls) -> "Portfolio":
        """
        Create a new portfolio for a newborn.

        Returns:
            Portfolio: New portfolio with corporate seed
        """
        return cls(
            seed_balance=CORPORATE_SEED,
            family_balance=0.0,
            age_years=0,
            months_active=0,
        )

    def add_family_contribution(self, amount: float):
        """
        Add family contribution (capped at MAX_FAMILY_CONTRIBUTION per month).

        Args:
            amount: Contribution amount
        """
        capped_amount = min(amount, MAX_FAMILY_CONTRIBUTION)
        self.family_balance += capped_amount

    def apply_return(self, annual_return: float):
        """
        Apply annual return to both portfolios.

        Args:
            annual_return: Annual return rate (e.g., 0.13 for 13%)
        """
        self.seed_balance *= (1 + annual_return)
        self.family_balance *= (1 + annual_return)

    def age_one_year(self):
        """Increment age by one year."""
        self.age_years += 1
        self.months_active += 12

    def total_balance(self) -> float:
        """Get total portfolio balance."""
        return self.seed_balance + self.family_balance

    def __repr__(self) -> str:
        return (
            f"Portfolio(age={self.age_years}, "
            f"seed=${self.seed_balance:,.0f}, "
            f"family=${self.family_balance:,.0f}, "
            f"total=${self.total_balance():,.0f})"
        )


@dataclass
class Cohort:
    """
    Represents a yearly cohort of children (all born in same year).

    Each cohort contains ~3.6M children who all receive identical returns.
    """

    birth_year: int
    cohort_id: int
    num_children: int
    seed_portfolio: float
    family_portfolio: float
    age_years: int = 0
    aged_out: bool = False

    @classmethod
    def create_new(cls, birth_year: int, cohort_id: int, num_children: int) -> "Cohort":
        """
        Create a new cohort.

        Args:
            birth_year: Calendar year of birth
            cohort_id: Sequential cohort identifier
            num_children: Number of children in cohort

        Returns:
            Cohort: New cohort with corporate seed
        """
        return cls(
            birth_year=birth_year,
            cohort_id=cohort_id,
            num_children=num_children,
            seed_portfolio=CORPORATE_SEED,
            family_portfolio=0.0,
            age_years=0,
            aged_out=False,
        )

    def add_monthly_contributions(self, months: int = 12):
        """
        Add family contributions for the year.

        Args:
            months: Number of months of contributions (default 12)
        """
        total_contribution = MAX_FAMILY_CONTRIBUTION * months
        self.family_portfolio += total_contribution

    def apply_return(self, annual_return: float):
        """
        Apply annual return to cohort portfolios.

        Args:
            annual_return: Annual return rate (e.g., 0.13 for 13%)
        """
        self.seed_portfolio *= (1 + annual_return)
        self.family_portfolio *= (1 + annual_return)

    def age_one_year(self):
        """Increment age by one year."""
        self.age_years += 1

    def total_per_child(self) -> float:
        """Get total balance per child."""
        return self.seed_portfolio + self.family_portfolio

    def seed_only_per_child(self) -> float:
        """Get seed-only balance per child."""
        return self.seed_portfolio

    def family_only_per_child(self) -> float:
        """Get family contribution balance per child."""
        return self.family_portfolio

    def __repr__(self) -> str:
        return (
            f"Cohort(id={self.cohort_id}, year={self.birth_year}, "
            f"age={self.age_years}, n={self.num_children:,}, "
            f"seed=${self.seed_portfolio:,.0f}, "
            f"family=${self.family_portfolio:,.0f})"
        )
