"""
Fairness Policy — Unified Fairness Enforcement

Master fairness orchestrator combining:
- Contribution caps
- Cohort equalization
- Quarterly rebalancing schedule
- Fairness metrics and compliance reporting

DNA Source: Economic justice + CO-HERE-US equality principles
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np

from .contribution_cap import ContributionCap, CapConfig
from .cohort_equalizer import CohortEqualizer, EqualizationConfig


@dataclass
class FairnessMetrics:
    """Comprehensive fairness metrics."""
    cycle: int

    # Contribution fairness
    avg_contribution: float
    contribution_gini: float
    accounts_at_cap: int
    total_refunds: float

    # Cohort fairness
    cohort_variance: float
    cohort_gini: float
    cohort_disparity: float
    equalization_quality: str

    # Compliance
    cap_compliant: bool
    variance_compliant: bool
    overall_compliant: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FairnessPolicy:
    """
    Master fairness policy enforcer.

    Integrates contribution caps and cohort equalization into
    a unified fairness system with quarterly rebalancing.

    Usage:
        policy = FairnessPolicy(
            n_cohorts=12,
            cap_config=CapConfig(monthly_cap_usd=20.0),
            equalization_config=EqualizationConfig()
        )

        # Each cycle
        result = policy.process_cycle(
            cycle=10,
            month=2,
            cohort_returns={0: 0.07, 1: 0.06, ...},
            contributions={"user1": 15.0, "user2": 18.0, ...},
            cohort_assignments={"user1": 0, "user2": 1, ...}
        )

        # Get fairness report
        report = policy.get_fairness_report()
    """

    def __init__(
        self,
        n_cohorts: int,
        cap_config: Optional[CapConfig] = None,
        equalization_config: Optional[EqualizationConfig] = None,
        quarterly_rebalance: bool = True
    ):
        """
        Initialize fairness policy.

        Args:
            n_cohorts: Number of cohorts
            cap_config: Contribution cap configuration
            equalization_config: Equalization configuration
            quarterly_rebalance: Enable quarterly rebalancing schedule
        """
        self.n_cohorts = n_cohorts
        self.quarterly_rebalance = quarterly_rebalance

        # Initialize components
        self.cap_enforcer = ContributionCap(config=cap_config)
        self.equalizer = CohortEqualizer(
            n_cohorts=n_cohorts,
            config=equalization_config
        )

        # Metrics history
        self.metrics_history: List[FairnessMetrics] = []

    def process_cycle(
        self,
        cycle: int,
        month: int,
        cohort_returns: Dict[int, float],
        contributions: Dict[str, float],
        cohort_assignments: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Process a cycle with fairness enforcement.

        Args:
            cycle: Cycle number
            month: Month number (0-11)
            cohort_returns: Dict mapping cohort_id -> return
            contributions: Dict mapping account_id -> contribution amount
            cohort_assignments: Dict mapping account_id -> cohort_id

        Returns:
            Dict with fairness actions and metrics
        """
        result = {
            "cycle": cycle,
            "month": month,
            "cap_actions": [],
            "equalization_actions": {},
            "rebalance_ids": [],
            "metrics": None,
        }

        # 1. Enforce contribution caps
        for account_id, amount in contributions.items():
            cap_result = self.cap_enforcer.record_contribution(
                account_id=account_id,
                amount=amount,
                month=month
            )

            if cap_result["refund_due"]:
                result["cap_actions"].append({
                    "account_id": account_id,
                    "refund": cap_result.get("refund_issued", 0.0),
                    "reason": "monthly_cap_exceeded",
                })

        # 2. Record cohort returns
        self.equalizer.record_returns(cohort_returns, cycle)

        # 3. Compute equalization adjustments
        adjustments = self.equalizer.compute_adjustments(cohort_returns, cycle)
        result["equalization_actions"] = adjustments

        # 4. Determine rebalancing schedule
        if self._should_rebalance(cycle, month):
            # Quarterly rebalancing (25% of cohorts)
            available_slots = max(1, self.n_cohorts // 4)

            priority_ids = self.equalizer.get_rebalance_priority(
                cohort_returns=cohort_returns,
                available_slots=available_slots,
                cycle=cycle
            )

            result["rebalance_ids"] = priority_ids
            self.equalizer.mark_rebalanced(priority_ids, cycle)

        # 5. Compute fairness metrics
        metrics = self._compute_metrics(
            cycle=cycle,
            cohort_returns=cohort_returns,
            contributions=contributions
        )

        result["metrics"] = metrics
        self.metrics_history.append(metrics)

        return result

    def get_fairness_report(
        self,
        last_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive fairness report.

        Args:
            last_n: Include only last N cycles (None = all)

        Returns:
            Dict with fairness summary
        """
        if not self.metrics_history:
            return {
                "n_cycles": 0,
                "contribution_fairness": {},
                "cohort_fairness": {},
                "compliance": {},
                "trends": {},
            }

        history = self.metrics_history[-last_n:] if last_n else self.metrics_history

        # Aggregate metrics
        cohort_variances = [m.cohort_variance for m in history]
        cohort_ginis = [m.cohort_gini for m in history]
        contribution_ginis = [m.contribution_gini for m in history]

        return {
            "n_cycles": len(history),
            "contribution_fairness": {
                "avg_contribution": float(np.mean([m.avg_contribution for m in history])),
                "contribution_gini": float(np.mean(contribution_ginis)),
                "total_refunds": sum(m.total_refunds for m in history),
                "accounts_at_cap": history[-1].accounts_at_cap if history else 0,
            },
            "cohort_fairness": {
                "current_variance": history[-1].cohort_variance if history else 0.0,
                "avg_variance": float(np.mean(cohort_variances)),
                "avg_gini": float(np.mean(cohort_ginis)),
                "current_disparity": history[-1].cohort_disparity if history else 0.0,
                "quality": history[-1].equalization_quality if history else "unknown",
            },
            "compliance": {
                "cap_compliant": history[-1].cap_compliant if history else False,
                "variance_compliant": history[-1].variance_compliant if history else False,
                "overall_compliant": history[-1].overall_compliant if history else False,
                "compliance_rate": sum(1 for m in history if m.overall_compliant) / len(history),
            },
            "trends": {
                "variance_trend": self._compute_trend(cohort_variances),
                "gini_trend": self._compute_trend(cohort_ginis),
            },
        }

    def get_account_fairness(
        self,
        account_id: str,
        cohort_id: int
    ) -> Dict[str, Any]:
        """
        Get fairness status for a specific account.

        Args:
            account_id: Account identifier
            cohort_id: Account's cohort

        Returns:
            Dict with account fairness info
        """
        # Contribution history
        contrib_history = self.cap_enforcer.get_contribution_history(account_id)
        refund_history = self.cap_enforcer.get_refund_history(account_id)

        # Cohort performance
        cohort_returns = self.equalizer.cumulative_returns.get(cohort_id, [])

        return {
            "account_id": account_id,
            "cohort_id": cohort_id,
            "total_contributions": sum(contrib_history.values()),
            "total_refunds": sum(refund_history.values()),
            "months_contributed": len(contrib_history),
            "months_at_cap": sum(1 for amt in contrib_history.values() if amt >= 19.0),
            "cohort_avg_return": float(np.mean(cohort_returns)) if cohort_returns else 0.0,
            "cohort_total_cycles": len(cohort_returns),
        }

    def _should_rebalance(self, cycle: int, month: int) -> bool:
        """Determine if rebalancing should occur this cycle."""
        if not self.quarterly_rebalance:
            return True

        # Quarterly rebalancing: months 0, 3, 6, 9
        return month % 3 == 0

    def _compute_metrics(
        self,
        cycle: int,
        cohort_returns: Dict[int, float],
        contributions: Dict[str, float]
    ) -> FairnessMetrics:
        """Compute comprehensive fairness metrics."""
        # Cap metrics
        cap_stats = self.cap_enforcer.get_system_stats()

        # Contribution Gini
        if contributions:
            contrib_values = np.array(list(contributions.values()))
            contrib_gini = self._gini(contrib_values)
        else:
            contrib_gini = 0.0

        # Cohort metrics
        equity_report = self.equalizer.get_equity_report(cohort_returns)
        variance_check = self.equalizer.check_variance_compliance(cohort_returns)

        # Compliance
        cap_compliant = cap_stats["accounts_at_cap"] / max(1, cap_stats["total_accounts"]) < 0.5
        variance_compliant = variance_check["compliant"]
        overall_compliant = cap_compliant and variance_compliant

        return FairnessMetrics(
            cycle=cycle,
            avg_contribution=cap_stats["avg_monthly_contribution"],
            contribution_gini=contrib_gini,
            accounts_at_cap=cap_stats["accounts_at_cap"],
            total_refunds=cap_stats["total_refunds"],
            cohort_variance=equity_report["current_variance"],
            cohort_gini=equity_report["gini_coefficient"],
            cohort_disparity=equity_report["disparity"],
            equalization_quality=equity_report["quality"],
            cap_compliant=cap_compliant,
            variance_compliant=variance_compliant,
            overall_compliant=overall_compliant,
        )

    def _gini(self, values: np.ndarray) -> float:
        """Compute Gini coefficient."""
        if len(values) == 0:
            return 0.0

        sorted_values = np.sort(values)
        n = len(values)
        index = np.arange(1, n + 1)

        if np.sum(sorted_values) < 1e-9:
            return 0.0

        gini = (2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n

        return float(gini)

    def _compute_trend(self, values: List[float]) -> str:
        """Compute trend direction for a time series."""
        if len(values) < 2:
            return "unknown"

        recent = values[-min(10, len(values)):]
        x = np.arange(len(recent))
        slope, _ = np.polyfit(x, recent, 1)

        if abs(slope) < 0.0001:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"


# Example usage
if __name__ == "__main__":
    print("Testing Fairness Policy...")

    policy = FairnessPolicy(
        n_cohorts=12,
        cap_config=CapConfig(monthly_cap_usd=20.0),
        equalization_config=EqualizationConfig(),
        quarterly_rebalance=True
    )

    # Simulate 24 months (2 years) of operation
    print("\n1. Simulating 24 months of operation:")
    np.random.seed(42)

    n_accounts = 100

    for cycle in range(24):
        month = cycle % 12

        # Generate cohort returns (with some inequality)
        cohort_returns = {}
        for i in range(12):
            base = 0.07
            bias = (i - 6) * 0.001  # Small systematic difference
            noise = np.random.randn() * 0.01
            cohort_returns[i] = base + bias + noise

        # Generate contributions
        contributions = {}
        cohort_assignments = {}

        for account_id in range(n_accounts):
            # Random contribution amount
            amount = np.random.uniform(10, 25)  # Some will exceed cap
            contributions[f"user{account_id}"] = amount

            # Assign to cohort
            cohort_assignments[f"user{account_id}"] = account_id % 12

        # Process cycle
        result = policy.process_cycle(
            cycle=cycle,
            month=month,
            cohort_returns=cohort_returns,
            contributions=contributions,
            cohort_assignments=cohort_assignments
        )

        if cycle in [0, 12, 23]:
            metrics = result["metrics"]
            print(f"  Cycle {cycle} (month {month}):")
            print(f"    Cohort variance: {metrics.cohort_variance:.6f}")
            print(f"    Contribution Gini: {metrics.contribution_gini:.4f}")
            print(f"    Refunds issued: ${metrics.total_refunds:.2f}")
            print(f"    Rebalanced cohorts: {len(result['rebalance_ids'])}")
            print(f"    Overall compliant: {metrics.overall_compliant}")

    # Final fairness report
    print("\n2. Final fairness report (last 12 months):")
    report = policy.get_fairness_report(last_n=12)

    print(f"\n  Contribution Fairness:")
    print(f"    Avg contribution: ${report['contribution_fairness']['avg_contribution']:.2f}")
    print(f"    Contribution Gini: {report['contribution_fairness']['contribution_gini']:.4f}")
    print(f"    Total refunds: ${report['contribution_fairness']['total_refunds']:.2f}")
    print(f"    Accounts at cap: {report['contribution_fairness']['accounts_at_cap']}")

    print(f"\n  Cohort Fairness:")
    print(f"    Current variance: {report['cohort_fairness']['current_variance']:.6f}")
    print(f"    Avg variance: {report['cohort_fairness']['avg_variance']:.6f}")
    print(f"    Current disparity: {report['cohort_fairness']['current_disparity']:.4f}")
    print(f"    Quality: {report['cohort_fairness']['quality']}")

    print(f"\n  Compliance:")
    print(f"    Cap compliant: {report['compliance']['cap_compliant']}")
    print(f"    Variance compliant: {report['compliance']['variance_compliant']}")
    print(f"    Overall compliant: {report['compliance']['overall_compliant']}")
    print(f"    Compliance rate: {report['compliance']['compliance_rate']:.1%}")

    print(f"\n  Trends:")
    print(f"    Variance trend: {report['trends']['variance_trend']}")
    print(f"    Gini trend: {report['trends']['gini_trend']}")

    # Individual account fairness
    print("\n3. Sample account fairness (user0):")
    account_fairness = policy.get_account_fairness("user0", cohort_id=0)
    print(f"  Total contributions: ${account_fairness['total_contributions']:.2f}")
    print(f"  Total refunds: ${account_fairness['total_refunds']:.2f}")
    print(f"  Months contributed: {account_fairness['months_contributed']}")
    print(f"  Cohort avg return: {account_fairness['cohort_avg_return']:.4f}")

    print("\n✓ Fairness Policy operational")
