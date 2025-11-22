"""
Contribution Cap — $20/Month Maximum Enforcement

Ensures no participant contributes more than $20/month to the system,
maintaining affordability and fairness.

DNA Source: Economic accessibility requirements
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import numpy as np


@dataclass
class CapConfig:
    """Contribution cap configuration."""
    monthly_cap_usd: float = 20.0  # $20/mo maximum
    annual_cap_usd: Optional[float] = None  # Auto-computed if None
    grace_period_months: int = 1  # Allow 1-month overage grace
    refund_threshold: float = 0.01  # Refund if overage > $0.01


class ContributionCap:
    """
    Contribution cap enforcer.

    Tracks individual contributions and enforces monthly/annual caps
    with automatic refunds for overages.

    Usage:
        cap = ContributionCap(config=CapConfig(monthly_cap_usd=20.0))

        # Check if contribution allowed
        allowed, max_amount = cap.check_contribution(
            account_id="user123",
            amount=15.0,
            month=0
        )

        # Record contribution
        if allowed:
            cap.record_contribution(
                account_id="user123",
                amount=15.0,
                month=0
            )

        # Get refund if exceeded
        refund = cap.compute_refund(account_id="user123", month=0)
    """

    def __init__(self, config: Optional[CapConfig] = None):
        """
        Initialize contribution cap enforcer.

        Args:
            config: Cap configuration
        """
        self.config = config or CapConfig()

        # Auto-compute annual cap if not specified
        if self.config.annual_cap_usd is None:
            self.config.annual_cap_usd = self.config.monthly_cap_usd * 12

        # Track contributions: account_id -> {month -> amount}
        self.contributions: Dict[str, Dict[int, float]] = {}

        # Track refunds issued
        self.refunds: Dict[str, Dict[int, float]] = {}

    def check_contribution(
        self,
        account_id: str,
        amount: float,
        month: int
    ) -> tuple[bool, float]:
        """
        Check if contribution is allowed under cap.

        Args:
            account_id: Account identifier
            amount: Proposed contribution amount
            month: Month number (0-11)

        Returns:
            (allowed, max_allowed_amount)
        """
        current_month_total = self._get_month_total(account_id, month)
        remaining = self.config.monthly_cap_usd - current_month_total

        if remaining <= 0:
            return False, 0.0

        if amount <= remaining:
            return True, amount

        # Partial contribution allowed up to cap
        return True, remaining

    def record_contribution(
        self,
        account_id: str,
        amount: float,
        month: int
    ) -> Dict[str, Any]:
        """
        Record a contribution.

        Args:
            account_id: Account identifier
            amount: Contribution amount
            month: Month number

        Returns:
            Dict with status and overage info
        """
        if account_id not in self.contributions:
            self.contributions[account_id] = {}

        current = self.contributions[account_id].get(month, 0.0)
        new_total = current + amount

        self.contributions[account_id][month] = new_total

        # Check for overage
        overage = max(0, new_total - self.config.monthly_cap_usd)

        result = {
            "account_id": account_id,
            "month": month,
            "amount": amount,
            "month_total": new_total,
            "cap": self.config.monthly_cap_usd,
            "overage": overage,
            "refund_due": overage >= self.config.refund_threshold,
        }

        # Auto-issue refund if needed
        if result["refund_due"]:
            self._issue_refund(account_id, month, overage)
            result["refund_issued"] = overage

        return result

    def compute_refund(self, account_id: str, month: int) -> float:
        """
        Compute refund owed for a month.

        Args:
            account_id: Account identifier
            month: Month number

        Returns:
            Refund amount
        """
        total = self._get_month_total(account_id, month)
        overage = max(0, total - self.config.monthly_cap_usd)

        if overage >= self.config.refund_threshold:
            return overage

        return 0.0

    def get_annual_total(self, account_id: str, year_months: List[int]) -> float:
        """
        Get total contributions for a year.

        Args:
            account_id: Account identifier
            year_months: List of month numbers in the year

        Returns:
            Total annual contribution
        """
        if account_id not in self.contributions:
            return 0.0

        total = sum(
            self.contributions[account_id].get(m, 0.0)
            for m in year_months
        )

        return total

    def check_annual_cap(
        self,
        account_id: str,
        year_months: List[int]
    ) -> Dict[str, Any]:
        """
        Check annual cap compliance.

        Args:
            account_id: Account identifier
            year_months: Months in the year (e.g., [0, 1, 2, ..., 11])

        Returns:
            Dict with annual cap status
        """
        annual_total = self.get_annual_total(account_id, year_months)
        annual_cap = self.config.annual_cap_usd

        return {
            "account_id": account_id,
            "annual_total": annual_total,
            "annual_cap": annual_cap,
            "under_cap": annual_total <= annual_cap,
            "overage": max(0, annual_total - annual_cap),
        }

    def get_contribution_history(
        self,
        account_id: str
    ) -> Dict[int, float]:
        """
        Get contribution history for an account.

        Args:
            account_id: Account identifier

        Returns:
            Dict mapping month -> amount
        """
        return self.contributions.get(account_id, {}).copy()

    def get_refund_history(
        self,
        account_id: str
    ) -> Dict[int, float]:
        """
        Get refund history for an account.

        Args:
            account_id: Account identifier

        Returns:
            Dict mapping month -> refund amount
        """
        return self.refunds.get(account_id, {}).copy()

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system-wide cap statistics.

        Returns:
            Dict with aggregate stats
        """
        total_accounts = len(self.contributions)

        if total_accounts == 0:
            return {
                "total_accounts": 0,
                "total_contributions": 0.0,
                "total_refunds": 0.0,
                "accounts_at_cap": 0,
                "avg_monthly_contribution": 0.0,
            }

        # Compute aggregates
        all_contributions = []
        accounts_at_cap = 0

        for account_id, months in self.contributions.items():
            for month, amount in months.items():
                all_contributions.append(amount)
                if amount >= self.config.monthly_cap_usd * 0.99:  # 99% of cap
                    accounts_at_cap += 1

        total_refunds = sum(
            sum(refunds.values())
            for refunds in self.refunds.values()
        )

        return {
            "total_accounts": total_accounts,
            "total_contributions": sum(all_contributions),
            "total_refunds": total_refunds,
            "accounts_at_cap": accounts_at_cap,
            "avg_monthly_contribution": np.mean(all_contributions) if all_contributions else 0.0,
            "median_monthly_contribution": np.median(all_contributions) if all_contributions else 0.0,
        }

    def _get_month_total(self, account_id: str, month: int) -> float:
        """Get total contributions for an account in a month."""
        if account_id not in self.contributions:
            return 0.0
        return self.contributions[account_id].get(month, 0.0)

    def _issue_refund(self, account_id: str, month: int, amount: float) -> None:
        """Issue a refund."""
        if account_id not in self.refunds:
            self.refunds[account_id] = {}

        current_refund = self.refunds[account_id].get(month, 0.0)
        self.refunds[account_id][month] = current_refund + amount


# Example usage
if __name__ == "__main__":
    print("Testing Contribution Cap...")

    cap = ContributionCap(config=CapConfig(monthly_cap_usd=20.0))

    # Test normal contributions
    print("\n1. Normal contributions:")
    for month in range(3):
        result = cap.record_contribution(
            account_id="alice",
            amount=15.0,
            month=month
        )
        print(f"  Month {month}: ${result['amount']:.2f}, "
              f"total=${result['month_total']:.2f}, "
              f"overage=${result['overage']:.2f}")

    # Test cap enforcement
    print("\n2. Cap enforcement (trying to contribute $25 in month 3):")
    allowed, max_amt = cap.check_contribution("alice", 25.0, month=3)
    print(f"  Allowed: {allowed}, Max allowed: ${max_amt:.2f}")

    result = cap.record_contribution("alice", max_amt, month=3)
    print(f"  Recorded: ${result['amount']:.2f}, "
          f"total=${result['month_total']:.2f}")

    # Test overage with refund
    print("\n3. Overage with automatic refund:")
    result = cap.record_contribution("bob", 25.0, month=0)
    print(f"  Contributed: ${result['amount']:.2f}")
    print(f"  Month total: ${result['month_total']:.2f}")
    print(f"  Overage: ${result['overage']:.2f}")
    print(f"  Refund issued: ${result.get('refund_issued', 0.0):.2f}")

    # Annual cap check
    print("\n4. Annual cap check:")
    # Contribute max each month for a year
    for month in range(12):
        cap.record_contribution("charlie", 20.0, month=month)

    annual_check = cap.check_annual_cap("charlie", list(range(12)))
    print(f"  Annual total: ${annual_check['annual_total']:.2f}")
    print(f"  Annual cap: ${annual_check['annual_cap']:.2f}")
    print(f"  Under cap: {annual_check['under_cap']}")

    # System stats
    print("\n5. System-wide statistics:")
    stats = cap.get_system_stats()
    print(f"  Total accounts: {stats['total_accounts']}")
    print(f"  Total contributions: ${stats['total_contributions']:.2f}")
    print(f"  Total refunds: ${stats['total_refunds']:.2f}")
    print(f"  Accounts at cap: {stats['accounts_at_cap']}")
    print(f"  Avg monthly contribution: ${stats['avg_monthly_contribution']:.2f}")

    # Contribution history
    print("\n6. Contribution history (alice):")
    history = cap.get_contribution_history("alice")
    for month, amount in sorted(history.items()):
        print(f"  Month {month}: ${amount:.2f}")

    print("\n✓ Contribution Cap operational")
