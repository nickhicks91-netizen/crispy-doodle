"""
Contribution History — Per-Cohort Performance Tracking

Tracks individual cohort contributions, returns, and rebalance events.
Enables fairness verification and equity tracking.

DNA Source: Financial transparency requirements
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, field
import time


@dataclass
class CohortContribution:
    """Single cohort contribution record."""
    cohort_id: int
    cycle: int
    timestamp: float
    return_value: float  # Cohort return for this cycle
    portfolio_value: float  # Total portfolio value
    rebalanced: bool  # Whether rebalanced this cycle
    damping_mod: float  # PLF damping modifier applied
    phase: float  # Cohort phase
    charge: float  # Fracton charge


class ContributionTracker:
    """
    Per-cohort contribution and performance tracker.

    Maintains historical records of cohort performance, rebalancing,
    and equity for transparency and fairness verification.

    Usage:
        tracker = ContributionTracker(n_cohorts=12)
        tracker.record_contribution(
            cohort_id=0,
            cycle=1,
            return_value=0.07,
            portfolio_value=10500.0,
            rebalanced=True,
            metadata={...}
        )
        history = tracker.get_cohort_history(cohort_id=0)
        equity = tracker.compute_equity_metrics(last_n=25)
    """

    def __init__(self, n_cohorts: int):
        """
        Initialize contribution tracker.

        Args:
            n_cohorts: Number of cohorts to track
        """
        self.n_cohorts = n_cohorts
        self.contributions: Dict[int, List[CohortContribution]] = defaultdict(list)
        self.global_metrics: List[Dict[str, float]] = []

    def record_contribution(
        self,
        cohort_id: int,
        cycle: int,
        return_value: float,
        portfolio_value: float,
        rebalanced: bool,
        metadata: Optional[Dict[str, float]] = None,
        timestamp: Optional[float] = None
    ) -> None:
        """
        Record a cohort contribution for a cycle.

        Args:
            cohort_id: Cohort identifier
            cycle: Cycle/year number
            return_value: Return for this cohort this cycle
            portfolio_value: Total portfolio value
            rebalanced: Whether cohort was rebalanced
            metadata: Additional metrics (damping_mod, phase, charge, etc.)
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()

        if metadata is None:
            metadata = {}

        contrib = CohortContribution(
            cohort_id=cohort_id,
            cycle=cycle,
            timestamp=timestamp,
            return_value=return_value,
            portfolio_value=portfolio_value,
            rebalanced=rebalanced,
            damping_mod=metadata.get("damping_mod", 1.0),
            phase=metadata.get("phase", 0.0),
            charge=metadata.get("charge", 0.0),
        )

        self.contributions[cohort_id].append(contrib)

    def record_global_metrics(self, cycle: int, metrics: Dict[str, float]) -> None:
        """
        Record system-wide metrics for a cycle.

        Args:
            cycle: Cycle number
            metrics: Global metrics (mean return, variance, etc.)
        """
        metrics_copy = metrics.copy()
        metrics_copy["cycle"] = cycle
        self.global_metrics.append(metrics_copy)

    def get_cohort_history(
        self,
        cohort_id: int,
        last_n: Optional[int] = None
    ) -> List[CohortContribution]:
        """
        Get contribution history for a specific cohort.

        Args:
            cohort_id: Cohort identifier
            last_n: Return only last N records

        Returns:
            List of CohortContribution records
        """
        history = self.contributions.get(cohort_id, [])

        if last_n is not None:
            history = history[-last_n:]

        return history

    def get_cohort_returns(
        self,
        cohort_id: int,
        last_n: Optional[int] = None
    ) -> np.ndarray:
        """
        Get return time series for a cohort.

        Args:
            cohort_id: Cohort identifier
            last_n: Return only last N values

        Returns:
            Array of returns
        """
        history = self.get_cohort_history(cohort_id, last_n=last_n)
        return np.array([c.return_value for c in history])

    def get_rebalance_events(
        self,
        cohort_id: int,
        last_n: Optional[int] = None
    ) -> List[int]:
        """
        Get cycles where cohort was rebalanced.

        Args:
            cohort_id: Cohort identifier
            last_n: Look back N cycles

        Returns:
            List of cycle numbers with rebalancing
        """
        history = self.get_cohort_history(cohort_id, last_n=last_n)
        return [c.cycle for c in history if c.rebalanced]

    def compute_equity_metrics(self, last_n: int = 25) -> Dict[str, Any]:
        """
        Compute equity and fairness metrics across all cohorts.

        Args:
            last_n: Analyze last N cycles

        Returns:
            Dict with equity metrics
        """
        if not self.contributions:
            return {}

        # Gather returns for all cohorts
        all_returns = {}
        for cohort_id in range(self.n_cohorts):
            returns = self.get_cohort_returns(cohort_id, last_n=last_n)
            if len(returns) > 0:
                all_returns[cohort_id] = returns

        if not all_returns:
            return {}

        # Compute mean returns per cohort
        mean_returns = {cid: np.mean(rets) for cid, rets in all_returns.items()}
        std_returns = {cid: np.std(rets) for cid, rets in all_returns.items()}

        # Cross-cohort variance (equity measure)
        cohort_means = np.array(list(mean_returns.values()))
        cross_cohort_variance = np.var(cohort_means)
        cross_cohort_std = np.std(cohort_means)

        # Gini coefficient (inequality measure)
        gini = self._compute_gini(cohort_means)

        # Min/max disparity
        min_return = np.min(cohort_means)
        max_return = np.max(cohort_means)
        disparity = max_return - min_return

        return {
            "cross_cohort_variance": float(cross_cohort_variance),
            "cross_cohort_std": float(cross_cohort_std),
            "gini_coefficient": float(gini),
            "min_cohort_return": float(min_return),
            "max_cohort_return": float(max_return),
            "disparity": float(disparity),
            "mean_returns": mean_returns,
            "std_returns": std_returns,
            "n_cohorts_analyzed": len(all_returns),
        }

    def get_rebalance_frequency(self, last_n: int = 25) -> Dict[int, float]:
        """
        Compute rebalance frequency per cohort.

        Args:
            last_n: Analyze last N cycles

        Returns:
            Dict mapping cohort_id to rebalance fraction
        """
        frequencies = {}

        for cohort_id in range(self.n_cohorts):
            history = self.get_cohort_history(cohort_id, last_n=last_n)
            if len(history) == 0:
                frequencies[cohort_id] = 0.0
            else:
                rebalances = sum(1 for c in history if c.rebalanced)
                frequencies[cohort_id] = rebalances / len(history)

        return frequencies

    def _compute_gini(self, values: np.ndarray) -> float:
        """
        Compute Gini coefficient for inequality measurement.

        Args:
            values: Array of values (e.g., cohort returns)

        Returns:
            Gini coefficient [0, 1], where 0 = perfect equality
        """
        if len(values) == 0:
            return 0.0

        sorted_values = np.sort(values)
        n = len(values)
        index = np.arange(1, n + 1)
        gini = (2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n

        return float(gini)

    def get_summary_table(self, last_n: int = 25) -> Dict[str, List[Any]]:
        """
        Get summary table for all cohorts.

        Args:
            last_n: Analyze last N cycles

        Returns:
            Dict with lists for table display (cohort_id, mean_return, std, rebal_freq)
        """
        equity = self.compute_equity_metrics(last_n=last_n)
        rebal_freq = self.get_rebalance_frequency(last_n=last_n)

        cohort_ids = []
        mean_returns = []
        std_returns = []
        rebal_freqs = []

        for cohort_id in range(self.n_cohorts):
            cohort_ids.append(cohort_id)
            mean_returns.append(equity["mean_returns"].get(cohort_id, 0.0))
            std_returns.append(equity["std_returns"].get(cohort_id, 0.0))
            rebal_freqs.append(rebal_freq.get(cohort_id, 0.0))

        return {
            "cohort_id": cohort_ids,
            "mean_return": mean_returns,
            "std_return": std_returns,
            "rebalance_frequency": rebal_freqs,
        }


# Example usage
if __name__ == "__main__":
    print("Testing Contribution Tracker...")

    tracker = ContributionTracker(n_cohorts=12)

    # Simulate 25 years of contributions
    print("\n1. Simulating 25 years of cohort contributions:")
    np.random.seed(42)

    for cycle in range(25):
        for cohort_id in range(12):
            # Simulate slightly different returns (testing equity)
            base_return = 0.07
            cohort_bias = (cohort_id - 6) * 0.001  # Small systematic difference
            noise = np.random.randn() * 0.02

            return_val = base_return + cohort_bias + noise

            # Simulate rebalancing (25% per cycle)
            rebalanced = np.random.rand() < 0.25

            tracker.record_contribution(
                cohort_id=cohort_id,
                cycle=cycle,
                return_value=return_val,
                portfolio_value=10000 * (1 + return_val),
                rebalanced=rebalanced,
                metadata={
                    "damping_mod": 1.0 + np.random.randn() * 0.05,
                    "phase": np.random.uniform(-np.pi, np.pi),
                    "charge": abs(np.random.randn() * 0.3),
                }
            )

    print(f"  Recorded {sum(len(v) for v in tracker.contributions.values())} total contributions")

    # Equity analysis
    print("\n2. Equity metrics (last 25 years):")
    equity = tracker.compute_equity_metrics(last_n=25)
    print(f"  Cross-cohort variance: {equity['cross_cohort_variance']:.6f}")
    print(f"  Cross-cohort std: {equity['cross_cohort_std']:.4f}")
    print(f"  Gini coefficient: {equity['gini_coefficient']:.4f}")
    print(f"  Disparity (max-min): {equity['disparity']:.4f}")
    print(f"  Min cohort return: {equity['min_cohort_return']:.4f}")
    print(f"  Max cohort return: {equity['max_cohort_return']:.4f}")

    # Rebalance frequency
    print("\n3. Rebalance frequency:")
    rebal_freq = tracker.get_rebalance_frequency(last_n=25)
    avg_freq = np.mean(list(rebal_freq.values()))
    print(f"  Average rebalance frequency: {avg_freq:.2%}")
    print(f"  Min: {min(rebal_freq.values()):.2%}, Max: {max(rebal_freq.values()):.2%}")

    # Summary table
    print("\n4. Summary table (first 3 cohorts):")
    summary = tracker.get_summary_table(last_n=25)
    print(f"  {'Cohort':<8} {'Mean Return':<12} {'Std':<12} {'Rebal Freq':<12}")
    print(f"  {'-'*48}")
    for i in range(min(3, len(summary["cohort_id"]))):
        print(f"  {summary['cohort_id'][i]:<8} "
              f"{summary['mean_return'][i]:<12.4f} "
              f"{summary['std_return'][i]:<12.4f} "
              f"{summary['rebalance_frequency'][i]:<12.2%}")

    # Individual cohort history
    print("\n5. Cohort 0 history (last 5 cycles):")
    history = tracker.get_cohort_history(cohort_id=0, last_n=5)
    for contrib in history:
        rebal_str = "✓" if contrib.rebalanced else " "
        print(f"  Cycle {contrib.cycle}: return={contrib.return_value:.4f}, "
              f"rebalanced=[{rebal_str}], charge={contrib.charge:.3f}")

    print("\n✓ Contribution Tracker operational")
