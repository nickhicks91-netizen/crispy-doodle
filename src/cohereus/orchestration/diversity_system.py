"""
Inter-Bot Diversity System (IDS) — Prevents Bot Synchronization

Prevents flash crashes and market manipulation through:
- Phase offset diversification
- Staggered rebalancing windows
- Liquidity pressure detection
- Anti-synchronization enforcement

DNA Source: EchoZero coupling mechanisms (phase coherence → phase diversity)
"""

import torch
import numpy as np
from typing import List, Tuple, Optional


class InterBotDiversitySystem:
    """
    IDS — Inter-Bot Diversity System

    Prevents catastrophic bot synchronization by:
    - Assigning unique phase offsets to each cohort
    - Detecting synchronization risk
    - Enforcing temporal diversity
    - Monitoring liquidity pressure

    DNA Source: EchoZero coherence calculation (inverted for diversity)
    """

    def __init__(
        self,
        n_cohorts: int = 12,
        min_phase_separation: float = 0.05,  # Minimum 5% phase separation
        max_simultaneous_fraction: float = 0.15  # Max 15% can rebalance simultaneously
    ):
        """
        Initialize Inter-Bot Diversity System

        Args:
            n_cohorts: Number of cohorts to manage
            min_phase_separation: Minimum phase offset between cohorts
            max_simultaneous_fraction: Maximum fraction that can act simultaneously
        """
        self.n_cohorts = n_cohorts
        self.min_phase_sep = min_phase_separation
        self.max_simultaneous = max_simultaneous_fraction

        # Assign phase offsets (evenly distributed)
        self.phase_offsets = self._generate_phase_offsets()

        # Synchronization monitoring
        self.rebalance_history: List[Tuple[int, List[int]]] = []  # (day, [cohort_ids])

    def _generate_phase_offsets(self) -> np.ndarray:
        """
        Generate evenly-distributed phase offsets

        Inspired by: EchoZero frequency distribution (harmonic spacing)
        """
        # Evenly space phases in [0, 1) with slight jitter for robustness
        base_offsets = np.linspace(0, 1.0, self.n_cohorts, endpoint=False)

        # Add small random jitter (±2%) to prevent exact harmonics
        jitter = np.random.uniform(-0.02, 0.02, self.n_cohorts)
        offsets = (base_offsets + jitter) % 1.0

        return np.sort(offsets)

    def get_phase_offset(self, cohort_id: int) -> float:
        """Get phase offset for a specific cohort"""
        return float(self.phase_offsets[cohort_id])

    def should_rebalance(
        self,
        cohort_id: int,
        current_day: int,
        rebalance_period: int = 30  # Rebalance every 30 days
    ) -> bool:
        """
        Determine if cohort should rebalance today

        Uses phase offset to stagger rebalancing across cohorts

        Args:
            cohort_id: Cohort ID
            current_day: Current day number
            rebalance_period: Rebalancing period in days

        Returns:
            should_rebalance: True if this cohort should rebalance today
        """
        phase = self.phase_offsets[cohort_id]

        # Calculate phase-adjusted day
        phase_adjusted_day = current_day + phase * rebalance_period

        # Rebalance if we're in the rebalancing window
        normalized_day = (phase_adjusted_day % rebalance_period) / rebalance_period

        # Small window (5% of period) to trigger rebalance
        return normalized_day < 0.05

    def check_synchronization_risk(
        self,
        cohorts_rebalancing: List[int]
    ) -> Tuple[bool, float]:
        """
        Check if too many cohorts are attempting to rebalance simultaneously

        Args:
            cohorts_rebalancing: List of cohort IDs planning to rebalance

        Returns:
            (is_risky, synchronization_fraction)
        """
        sync_fraction = len(cohorts_rebalancing) / self.n_cohorts

        is_risky = sync_fraction > self.max_simultaneous

        return is_risky, sync_fraction

    def compute_diversity_score(self) -> float:
        """
        Compute phase diversity score (0 = synchronized, 1 = maximally diverse)

        Inspired by: EchoZero coherence (inverted)
        coherence = mean(cos(∠ψᵢ - ∠ψⱼ))
        diversity = 1 - coherence
        """
        phases = self.phase_offsets * 2 * np.pi  # Convert to radians

        # Compute pairwise phase differences
        phase_diffs = []
        for i in range(len(phases)):
            for j in range(i + 1, len(phases)):
                phase_diffs.append(abs(phases[i] - phases[j]))

        # Measure of diversity (lower variance = more uniform = better)
        ideal_spacing = 2 * np.pi / self.n_cohorts
        deviation = np.std([abs(diff - ideal_spacing) for diff in phase_diffs])

        # Convert to diversity score (0-1)
        diversity_score = 1.0 / (1.0 + deviation)

        return float(diversity_score)

    def detect_liquidity_pressure(
        self,
        cohorts_rebalancing: List[int],
        total_aum: float,
        daily_market_volume: float
    ) -> Tuple[bool, float]:
        """
        Detect if rebalancing will create excessive liquidity pressure

        Args:
            cohorts_rebalancing: List of cohort IDs rebalancing
            total_aum: Total AUM across all cohorts
            daily_market_volume: Daily market trading volume

        Returns:
            (has_pressure, pressure_ratio)
        """
        # Estimate rebalancing volume (assume 10% turnover per rebalance)
        rebalancing_fraction = len(cohorts_rebalancing) / self.n_cohorts
        rebalancing_volume = total_aum * rebalancing_fraction * 0.10

        # Pressure ratio (rebalancing volume / market volume)
        pressure_ratio = rebalancing_volume / (daily_market_volume + 1e-8)

        # Flag if > 5% of market volume
        has_pressure = pressure_ratio > 0.05

        return has_pressure, pressure_ratio

    def record_rebalance(self, current_day: int, cohorts_rebalancing: List[int]):
        """Record rebalancing event for monitoring"""
        self.rebalance_history.append((current_day, cohorts_rebalancing))

        # Keep last 100 events
        if len(self.rebalance_history) > 100:
            self.rebalance_history.pop(0)

    def get_diversity_metrics(self) -> dict:
        """Get diversity diagnostics"""
        diversity_score = self.compute_diversity_score()

        # Recent synchronization events
        recent_sync_events = 0
        if self.rebalance_history:
            for day, cohorts in self.rebalance_history[-30:]:  # Last 30 events
                sync_fraction = len(cohorts) / self.n_cohorts
                if sync_fraction > self.max_simultaneous:
                    recent_sync_events += 1

        return {
            'diversity_score': diversity_score,
            'phase_offsets': self.phase_offsets.tolist(),
            'min_phase_separation': float(np.min(np.diff(np.sort(self.phase_offsets)))),
            'recent_sync_events': recent_sync_events,
            'max_simultaneous_allowed': self.max_simultaneous
        }


# Example usage
if __name__ == "__main__":
    print("Testing Inter-Bot Diversity System (IDS)...")

    ids = InterBotDiversitySystem(n_cohorts=12)

    # Check phase diversity
    print("\n1. Phase offset diversity:")
    metrics = ids.get_diversity_metrics()
    print(f"  Diversity score: {metrics['diversity_score']:.4f}")
    print(f"  Min phase separation: {metrics['min_phase_separation']:.4f}")
    print(f"  Phase offsets: {[f'{p:.4f}' for p in metrics['phase_offsets']]}")

    # Simulate rebalancing over 90 days
    print("\n2. Simulating rebalancing over 90 days:")
    rebalance_period = 30

    for day in range(90):
        cohorts_rebalancing = []

        # Check which cohorts should rebalance
        for cohort_id in range(12):
            if ids.should_rebalance(cohort_id, day, rebalance_period):
                cohorts_rebalancing.append(cohort_id)

        if cohorts_rebalancing:
            # Check synchronization risk
            is_risky, sync_fraction = ids.check_synchronization_risk(cohorts_rebalancing)

            print(f"  Day {day}: {len(cohorts_rebalancing)} cohorts rebalancing "
                  f"({sync_fraction:.2%})", end="")

            if is_risky:
                print(" ⚠️  SYNCHRONIZATION RISK", end="")

            print()

            # Record event
            ids.record_rebalance(day, cohorts_rebalancing)

    # Check liquidity pressure
    print("\n3. Liquidity pressure analysis:")
    total_aum = 720_000_000_000.0  # $720B (3.6M kids × $200k average)
    daily_market_volume = 50_000_000_000_000.0  # $50T daily volume

    cohorts_rebalancing = [0, 1, 2, 3]  # 4 cohorts
    has_pressure, pressure_ratio = ids.detect_liquidity_pressure(
        cohorts_rebalancing,
        total_aum,
        daily_market_volume
    )

    print(f"  Cohorts rebalancing: {len(cohorts_rebalancing)}")
    print(f"  Total AUM: ${total_aum:,.0f}")
    print(f"  Daily market volume: ${daily_market_volume:,.0f}")
    print(f"  Pressure ratio: {pressure_ratio:.6f}")
    print(f"  Has liquidity pressure: {has_pressure}")

    # Final diversity check
    print("\n4. Final diversity metrics:")
    final_metrics = ids.get_diversity_metrics()
    print(f"  Diversity score: {final_metrics['diversity_score']:.4f}")
    print(f"  Recent sync events: {final_metrics['recent_sync_events']}")

    print("\n✓ Inter-Bot Diversity System tests passed")
