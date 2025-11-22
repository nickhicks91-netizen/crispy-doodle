"""
Cohort Equalizer — Equal Outcomes Enforcement

Ensures all cohorts achieve nearly identical long-term outcomes
through variance targeting and rebalancing prioritization.

DNA Source: Economic equality principles + CO-HERE-US diversity layer
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class EqualizationConfig:
    """Equalization policy configuration."""
    target_variance: float = 0.01  # 1% cross-cohort variance target
    variance_tolerance: float = 0.012  # 1.2% tolerance before intervention
    rebalance_priority_threshold: float = 1.5  # Cohorts 50% behind get priority
    min_rebalance_interval: int = 3  # Minimum months between rebalances
    equalization_strength: float = 0.3  # Strength of equalization pull


class CohortEqualizer:
    """
    Cohort equalization enforcer.

    Actively manages cohort rebalancing to ensure equal long-term
    outcomes by prioritizing underperforming cohorts and dampening
    overperformers.

    Usage:
        equalizer = CohortEqualizer(
            n_cohorts=12,
            config=EqualizationConfig()
        )

        # Compute equalization adjustments
        adjustments = equalizer.compute_adjustments(
            cohort_returns={0: 0.08, 1: 0.06, 2: 0.07, ...},
            cycle=10
        )

        # Get priority rebalance schedule
        priority_ids = equalizer.get_rebalance_priority(
            cohort_returns={...},
            available_slots=3
        )
    """

    def __init__(
        self,
        n_cohorts: int,
        config: Optional[EqualizationConfig] = None
    ):
        """
        Initialize cohort equalizer.

        Args:
            n_cohorts: Number of cohorts
            config: Equalization configuration
        """
        self.n_cohorts = n_cohorts
        self.config = config or EqualizationConfig()

        # Track cohort history
        self.cumulative_returns: Dict[int, List[float]] = {
            i: [] for i in range(n_cohorts)
        }
        self.last_rebalance: Dict[int, int] = {
            i: -999 for i in range(n_cohorts)
        }

    def record_returns(
        self,
        cohort_returns: Dict[int, float],
        cycle: int
    ) -> None:
        """
        Record returns for all cohorts in a cycle.

        Args:
            cohort_returns: Dict mapping cohort_id -> return
            cycle: Current cycle number
        """
        for cohort_id, ret in cohort_returns.items():
            if cohort_id in self.cumulative_returns:
                self.cumulative_returns[cohort_id].append(ret)

    def compute_variance(
        self,
        cohort_returns: Dict[int, float]
    ) -> float:
        """
        Compute cross-cohort variance.

        Args:
            cohort_returns: Dict mapping cohort_id -> return

        Returns:
            Variance across cohorts
        """
        if not cohort_returns:
            return 0.0

        returns = np.array(list(cohort_returns.values()))
        return float(np.var(returns))

    def compute_adjustments(
        self,
        cohort_returns: Dict[int, float],
        cycle: int
    ) -> Dict[int, float]:
        """
        Compute equalization adjustments (damping modifiers).

        Args:
            cohort_returns: Current cohort returns
            cycle: Current cycle number

        Returns:
            Dict mapping cohort_id -> adjustment multiplier
        """
        if not cohort_returns:
            return {}

        returns = np.array([cohort_returns[i] for i in range(self.n_cohorts)])
        mean_return = np.mean(returns)

        adjustments = {}

        for cohort_id in range(self.n_cohorts):
            ret = cohort_returns.get(cohort_id, mean_return)

            # Compute deviation from mean
            deviation = ret - mean_return

            # Equalization adjustment (pull toward mean)
            # Underperformers get boost (>1.0), overperformers get damping (<1.0)
            adjustment = 1.0 - self.config.equalization_strength * (deviation / (abs(mean_return) + 1e-9))

            # Clamp to reasonable range [0.8, 1.2]
            adjustment = np.clip(adjustment, 0.8, 1.2)

            adjustments[cohort_id] = float(adjustment)

        return adjustments

    def get_rebalance_priority(
        self,
        cohort_returns: Dict[int, float],
        available_slots: int,
        cycle: int
    ) -> List[int]:
        """
        Get priority-ordered cohort IDs for rebalancing.

        Prioritizes cohorts that are underperforming and haven't
        been rebalanced recently.

        Args:
            cohort_returns: Current cohort returns
            available_slots: Number of rebalances available this cycle
            cycle: Current cycle number

        Returns:
            List of cohort IDs in priority order
        """
        if not cohort_returns:
            return []

        returns = np.array([cohort_returns[i] for i in range(self.n_cohorts)])
        mean_return = np.mean(returns)

        # Compute priority scores
        priority_scores = []

        for cohort_id in range(self.n_cohorts):
            ret = cohort_returns.get(cohort_id, mean_return)

            # Underperformance score (higher = more underperforming)
            underperformance = max(0, mean_return - ret)

            # Time since last rebalance
            cycles_since_rebalance = cycle - self.last_rebalance.get(cohort_id, -999)

            # Priority score (higher = more urgent)
            score = (
                underperformance * 10 +  # Heavily weight underperformance
                min(cycles_since_rebalance, 20) * 0.5  # Moderate time weight
            )

            # Only include if min interval has passed
            if cycles_since_rebalance >= self.config.min_rebalance_interval:
                priority_scores.append((cohort_id, score))

        # Sort by priority (highest first)
        priority_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top N
        return [cid for cid, _ in priority_scores[:available_slots]]

    def mark_rebalanced(self, cohort_ids: List[int], cycle: int) -> None:
        """
        Mark cohorts as rebalanced in this cycle.

        Args:
            cohort_ids: List of rebalanced cohort IDs
            cycle: Current cycle number
        """
        for cohort_id in cohort_ids:
            self.last_rebalance[cohort_id] = cycle

    def check_variance_compliance(
        self,
        cohort_returns: Dict[int, float]
    ) -> Dict[str, Any]:
        """
        Check if variance is within target.

        Args:
            cohort_returns: Current cohort returns

        Returns:
            Dict with compliance status
        """
        variance = self.compute_variance(cohort_returns)

        return {
            "variance": variance,
            "target": self.config.target_variance,
            "tolerance": self.config.variance_tolerance,
            "compliant": variance <= self.config.variance_tolerance,
            "intervention_needed": variance > self.config.variance_tolerance,
        }

    def get_equity_report(
        self,
        cohort_returns: Dict[int, float],
        window: int = 25
    ) -> Dict[str, Any]:
        """
        Generate equity report across cohorts.

        Args:
            cohort_returns: Current cohort returns
            window: Historical window for analysis

        Returns:
            Dict with equity metrics
        """
        # Current variance
        current_variance = self.compute_variance(cohort_returns)

        # Historical variance (if enough data)
        if all(len(rets) >= window for rets in self.cumulative_returns.values()):
            historical_returns = {
                cid: np.mean(rets[-window:])
                for cid, rets in self.cumulative_returns.items()
            }
            historical_variance = self.compute_variance(historical_returns)
        else:
            historical_variance = None

        # Min/max disparity
        if cohort_returns:
            returns = np.array(list(cohort_returns.values()))
            min_return = float(np.min(returns))
            max_return = float(np.max(returns))
            disparity = max_return - min_return
        else:
            min_return = 0.0
            max_return = 0.0
            disparity = 0.0

        # Gini coefficient
        gini = self._compute_gini(cohort_returns)

        return {
            "current_variance": current_variance,
            "historical_variance": historical_variance,
            "min_return": min_return,
            "max_return": max_return,
            "disparity": disparity,
            "gini_coefficient": gini,
            "compliant": current_variance <= self.config.variance_tolerance,
            "quality": self._variance_quality(current_variance),
        }

    def _compute_gini(self, cohort_returns: Dict[int, float]) -> float:
        """Compute Gini coefficient for returns."""
        if not cohort_returns:
            return 0.0

        returns = np.array(list(cohort_returns.values()))
        sorted_returns = np.sort(returns)
        n = len(returns)
        index = np.arange(1, n + 1)

        if np.sum(sorted_returns) < 1e-9:
            return 0.0

        gini = (2 * np.sum(index * sorted_returns)) / (n * np.sum(sorted_returns)) - (n + 1) / n

        return float(gini)

    def _variance_quality(self, variance: float) -> str:
        """Classify variance quality."""
        if variance < 0.008:
            return "excellent"
        elif variance < 0.01:
            return "good"
        elif variance < 0.012:
            return "acceptable"
        else:
            return "needs_improvement"


# Example usage
if __name__ == "__main__":
    print("Testing Cohort Equalizer...")

    equalizer = CohortEqualizer(
        n_cohorts=12,
        config=EqualizationConfig()
    )

    # Simulate 25 cycles with unequal returns
    print("\n1. Simulating 25 cycles with initial inequality:")
    np.random.seed(42)

    for cycle in range(25):
        # Create unequal returns (cohorts 0-5 underperform)
        cohort_returns = {}
        for i in range(12):
            base_return = 0.07
            bias = -0.02 if i < 6 else 0.01  # First 6 cohorts underperform
            noise = np.random.randn() * 0.01

            cohort_returns[i] = base_return + bias + noise

        # Record returns
        equalizer.record_returns(cohort_returns, cycle)

        # Compute adjustments
        adjustments = equalizer.compute_adjustments(cohort_returns, cycle)

        # Get rebalance priority (3 slots available)
        priority = equalizer.get_rebalance_priority(
            cohort_returns,
            available_slots=3,
            cycle=cycle
        )

        # Mark as rebalanced
        equalizer.mark_rebalanced(priority, cycle)

        if cycle in [0, 10, 24]:
            variance = equalizer.compute_variance(cohort_returns)
            print(f"  Cycle {cycle}: variance={variance:.6f}, "
                  f"priority_rebalance={priority[:3]}")

    # Final equity report
    print("\n2. Final equity report:")
    final_returns = cohort_returns  # From last cycle
    report = equalizer.get_equity_report(final_returns, window=25)
    print(f"  Current variance: {report['current_variance']:.6f}")
    print(f"  Historical variance (25-cycle): {report['historical_variance']:.6f}")
    print(f"  Disparity (max-min): {report['disparity']:.4f}")
    print(f"  Gini coefficient: {report['gini_coefficient']:.4f}")
    print(f"  Quality: {report['quality']}")
    print(f"  Compliant: {report['compliant']}")

    # Variance compliance check
    print("\n3. Variance compliance:")
    compliance = equalizer.check_variance_compliance(final_returns)
    print(f"  Variance: {compliance['variance']:.6f}")
    print(f"  Target: {compliance['target']:.6f}")
    print(f"  Tolerance: {compliance['tolerance']:.6f}")
    print(f"  Compliant: {compliance['compliant']}")
    print(f"  Intervention needed: {compliance['intervention_needed']}")

    # Equalization adjustments
    print("\n4. Sample equalization adjustments (cycle 24):")
    adjustments = equalizer.compute_adjustments(final_returns, cycle=24)
    for i in range(min(6, len(adjustments))):
        print(f"  Cohort {i}: adjustment={adjustments[i]:.4f}, "
              f"return={final_returns[i]:.4f}")

    print("\n✓ Cohort Equalizer operational")
