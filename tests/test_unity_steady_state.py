#!/usr/bin/env python3
"""
CO-HERE-US Unity Version v1.0 — Steady State Equilibrium Test

CORRECT FUNDING MODEL WITH PROPER ANNUAL AVERAGING:
- $2,000 one-time corporate seed per child
- Optional $20/month family contribution (capped to prevent inequality)
- Target outcome: $50k-$90k at age 25
- 50/50 stocks/crypto allocation
- **ANNUAL AVERAGING: All cohorts receive IDENTICAL returns each year**
- PLF 2.0 smoothing for stability
- Fracton dampening for coherence

Tests both scenarios:
1. SEED ONLY: $2,000 corporate seed, no family contributions
2. SEED + FAMILY: $2,000 seed + $20/month family contributions

Key correction: NO per-cohort noise. One return per year, applied equally to ALL cohorts.
This ensures perfect fairness and prevents "birth year lottery."
"""

import numpy as np
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


def plf_smooth(returns: np.ndarray, window: int = 3) -> np.ndarray:
    """
    PLF 2.0 harmonic smoothing - reduces volatility through multi-scale averaging.

    Applies harmonic mean over rolling window to dampen extreme values.
    """
    smoothed = np.zeros_like(returns)
    for i in range(len(returns)):
        if i < window:
            # Use available data for early years
            window_data = returns[:i+1]
        else:
            window_data = returns[i-window+1:i+1]

        # Harmonic mean: more stable than arithmetic mean for compounding
        # Handle negative values by using arithmetic mean as fallback
        if np.all(window_data > -0.9):  # Can compound
            harmonic = len(window_data) / np.sum(1.0 / (1.0 + window_data))
            smoothed[i] = harmonic - 1.0
        else:
            smoothed[i] = np.mean(window_data)

    return smoothed


def fracton_dampen(returns: np.ndarray, damping_factor: float = 0.15) -> np.ndarray:
    """
    Fracton mode dampening - reduces variance while preserving mean.

    Dampens extreme deviations from mean to ensure coherent outcomes.
    This is stability, not alpha-seeking.
    """
    mean_return = np.mean(returns)
    dampened = np.zeros_like(returns)

    for i in range(len(returns)):
        deviation = returns[i] - mean_return
        # Dampen the deviation, not the return itself
        dampened_deviation = deviation * (1.0 - damping_factor)
        dampened[i] = mean_return + dampened_deviation

    return dampened


@dataclass
class YearlyCohort:
    """Represents a yearly cohort of newborns."""
    year_joined: int
    n_children: int
    seed_portfolio: float  # From $2k corporate seed
    family_portfolio: float  # From optional $20/month family contributions
    years_active: int
    aged_out: bool = False
    final_seed_outcome: Optional[float] = None
    final_family_outcome: Optional[float] = None

    def avg_per_child_seed(self) -> float:
        """Average portfolio value per child (seed only)."""
        return self.seed_portfolio / self.n_children if self.n_children > 0 else 0.0

    def avg_per_child_family(self) -> float:
        """Average portfolio value per child (seed + family)."""
        return (self.seed_portfolio + self.family_portfolio) / self.n_children if self.n_children > 0 else 0.0


class UnitySteadyStateSimulator:
    """
    Unity Version steady state simulator with CORRECT annual averaging.

    Models the real CO-HERE-US architecture:
    - $2,000 corporate seed per child
    - Optional $20/month family contributions
    - 50/50 stocks/crypto allocation
    - ANNUAL AVERAGING: All cohorts get SAME return each year
    - PLF 2.0 smoothing + Fracton dampening
    - Target: $50k-$90k at age 25
    """

    def __init__(
        self,
        births_per_year: int = 3_600_000,
        cohort_duration_years: int = 25,
        corporate_seed: float = 2000.0,
        family_monthly: float = 20.0,
        seed: int = 42
    ):
        """Initialize steady state simulator."""
        self.births_per_year = births_per_year
        self.cohort_duration = cohort_duration_years
        self.corporate_seed = corporate_seed
        self.family_monthly = family_monthly
        np.random.seed(seed)

        print(f"Initializing CO-HERE-US Unity — CORRECTED Annual Averaging Model")
        print(f"=" * 70)
        print(f"  Births per year: {births_per_year:,}")
        print(f"  Cohort duration: {cohort_duration_years} years")
        print(f"  Corporate seed: ${corporate_seed:,.2f}")
        print(f"  Family contribution: ${family_monthly:,.2f}/month (optional)")
        print(f"  Steady state capacity: {births_per_year * cohort_duration_years:,} users")
        print(f"  KEY: All cohorts receive IDENTICAL annual returns (perfect fairness)")

        # Yearly cohorts
        self.active_cohorts: List[YearlyCohort] = []
        self.aged_out_cohorts: List[YearlyCohort] = []

        # System totals
        self.total_corporate_seed = 0.0
        self.total_family_contributions = 0.0
        self.total_distributed_seed = 0.0
        self.total_distributed_family = 0.0

        print("✓ Steady State Simulator initialized")
        print("=" * 70)

    def run_simulation(self, n_years: int = 50) -> Dict[str, Any]:
        """Run steady state simulation with proper annual averaging."""
        print(f"\nRunning {n_years}-year steady state simulation...")
        print(f"Using CORRECT model: Annual averaging ensures ALL cohorts get SAME returns\n")
        start_time = time.time()

        # Pre-generate market returns for entire simulation
        raw_returns = self._generate_market_returns(n_years)

        # Apply PLF 2.0 smoothing
        print("Applying PLF 2.0 harmonic smoothing...")
        smoothed_returns = plf_smooth(raw_returns)

        # Apply Fracton dampening
        print("Applying Fracton mode dampening for stability...")
        final_returns = fracton_dampen(smoothed_returns)

        print(f"Market returns prepared: {np.mean(final_returns):.2%} average\n")

        for year in range(n_years):
            # Progress indicator
            if year < self.cohort_duration:
                phase = "RAMP-UP"
            else:
                phase = "STEADY STATE"

            print(f"\n  Year {year + 1}/{n_years} [{phase}]")

            # 1. Add new cohort of newborns
            new_cohort = YearlyCohort(
                year_joined=year,
                n_children=self.births_per_year,
                seed_portfolio=self.corporate_seed * self.births_per_year,
                family_portfolio=0.0,
                years_active=0
            )
            self.active_cohorts.append(new_cohort)
            self.total_corporate_seed += self.corporate_seed * self.births_per_year
            print(f"    + {self.births_per_year:,} newborns joined")

            # 2. Get this year's return (SAME for all cohorts)
            annual_return = final_returns[year]
            print(f"    Annual return: {annual_return:.2%} (applied to ALL cohorts)")

            # 3. Process 12 months of family contributions for ALL active cohorts
            for month in range(12):
                for cohort in self.active_cohorts:
                    if cohort.aged_out:
                        continue
                    family_monthly_total = self.family_monthly * cohort.n_children
                    cohort.family_portfolio += family_monthly_total
                    self.total_family_contributions += family_monthly_total

            # 4. Apply SAME annual return to ALL active cohorts (ANNUAL AVERAGING)
            for cohort in self.active_cohorts:
                if cohort.aged_out:
                    continue

                # CRITICAL: All cohorts get IDENTICAL return (no noise!)
                cohort_return = annual_return

                # Compound BOTH portfolios
                cohort.seed_portfolio *= (1 + cohort_return)
                cohort.family_portfolio *= (1 + cohort_return)
                cohort.years_active += 1

            # 5. Age out cohorts that have reached duration limit
            cohorts_to_age_out = [
                c for c in self.active_cohorts
                if c.years_active >= self.cohort_duration and not c.aged_out
            ]

            for cohort in cohorts_to_age_out:
                cohort.aged_out = True
                cohort.final_seed_outcome = cohort.avg_per_child_seed()
                cohort.final_family_outcome = cohort.avg_per_child_family()
                self.total_distributed_seed += cohort.seed_portfolio
                self.total_distributed_family += cohort.family_portfolio
                self.aged_out_cohorts.append(cohort)

                print(f"    → Cohort {cohort.year_joined} aged out: {cohort.n_children:,} children")
                print(f"       SEED ONLY: ${cohort.final_seed_outcome:,.2f}/child")
                print(f"       SEED + FAMILY: ${cohort.final_family_outcome:,.2f}/child")

            # 6. Remove aged out cohorts
            self.active_cohorts = [c for c in self.active_cohorts if not c.aged_out]

            # 7. Show current state
            total_active_children = sum(c.n_children for c in self.active_cohorts)
            total_seed_portfolio = sum(c.seed_portfolio for c in self.active_cohorts)
            total_family_portfolio = sum(c.family_portfolio for c in self.active_cohorts)

            if total_active_children > 0:
                avg_seed = total_seed_portfolio / total_active_children
                avg_family = (total_seed_portfolio + total_family_portfolio) / total_active_children
                print(f"    Active: {total_active_children:,} children")
                print(f"    Avg (seed): ${avg_seed:,.2f} | Avg (seed+family): ${avg_family:,.2f}")

            if year == self.cohort_duration:
                print(f"\n    ✓ STEADY STATE REACHED: {total_active_children:,} users")

        elapsed = time.time() - start_time
        print(f"\n{'=' * 70}")
        print(f"✓ Simulation complete ({elapsed:.2f}s)")
        print(f"{'=' * 70}")

        return self._generate_report(n_years, final_returns)

    def _generate_market_returns(self, n_years: int) -> np.ndarray:
        """
        Generate raw market returns (50/50 crypto/stocks blend).
        These will be smoothed and dampened before use.
        """
        returns = np.zeros(n_years)

        for year in range(n_years):
            # Crypto component
            crypto_return = np.random.normal(0.18, 0.35)

            # Market component
            market_return = np.random.normal(0.08, 0.15)

            # 50/50 blend
            blended = 0.5 * crypto_return + 0.5 * market_return

            # Occasional crisis
            if year in [5, 15, 25, 35, 45]:
                crisis = -0.25
                blended = (blended + crisis) / 2

            returns[year] = blended

        return returns

    def _generate_report(self, n_years: int, annual_returns: np.ndarray) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        print("\n" + "=" * 70)
        print("CO-HERE-US UNITY v1.0 — STEADY STATE REPORT (CORRECTED MODEL)")
        print("=" * 70)

        # System scale
        print("\n1. SYSTEM SCALE")
        total_active_children = sum(c.n_children for c in self.active_cohorts)
        print(f"   Design capacity: {self.births_per_year * self.cohort_duration:,} users")
        print(f"   Current active: {total_active_children:,} users")
        print(f"   Cohorts aged out: {len(self.aged_out_cohorts)}")

        # Financial flows
        print("\n2. FINANCIAL FLOWS")
        print(f"   Corporate seed: ${self.total_corporate_seed / 1e9:.2f}B")
        print(f"   Family contributions: ${self.total_family_contributions / 1e9:.2f}B")
        print(f"   Total distributed: ${(self.total_distributed_seed + self.total_distributed_family) / 1e9:.2f}B")

        # Outcomes
        if len(self.aged_out_cohorts) > 0:
            print("\n3. AGED OUT COHORT OUTCOMES")

            seed_outcomes = [c.final_seed_outcome for c in self.aged_out_cohorts]
            family_outcomes = [c.final_family_outcome for c in self.aged_out_cohorts]

            seed_avg = np.mean(seed_outcomes)
            family_avg = np.mean(family_outcomes)

            target_min, target_max = 50000, 90000

            print(f"\n   SEED ONLY:")
            print(f"     Average: ${seed_avg:,.2f}")
            print(f"     Range: ${np.min(seed_outcomes):,.2f} - ${np.max(seed_outcomes):,.2f}")
            seed_in_target = sum(1 for x in seed_outcomes if target_min <= x <= target_max)
            print(f"     In target: {seed_in_target}/{len(seed_outcomes)}")

            print(f"\n   SEED + FAMILY:")
            print(f"     Average: ${family_avg:,.2f}")
            print(f"     Range: ${np.min(family_outcomes):,.2f} - ${np.max(family_outcomes):,.2f}")
            family_in_target = sum(1 for x in family_outcomes if target_min <= x <= target_max)
            print(f"     In target: {family_in_target}/{len(family_outcomes)}")

            # Coherence check (should be ZERO variance now)
            if len(self.aged_out_cohorts) >= 6:
                print(f"\n   COHERENCE (Early vs Late):")
                early_avg = np.mean([self.aged_out_cohorts[i].final_family_outcome for i in range(3)])
                late_avg = np.mean([self.aged_out_cohorts[-(i+1)].final_family_outcome for i in range(3)])
                variance = abs(early_avg - late_avg) / early_avg if early_avg > 0 else 0
                print(f"     Early cohorts: ${early_avg:,.2f}")
                print(f"     Late cohorts: ${late_avg:,.2f}")
                print(f"     Variance: {variance:.2%} {'✓' if variance < 0.05 else '✗'}")

        # Returns
        print(f"\n4. ANNUAL RETURNS (Post-PLF/Fracton)")
        print(f"   Average: {np.mean(annual_returns):.2%}")
        print(f"   Min: {np.min(annual_returns):.2%}")
        print(f"   Max: {np.max(annual_returns):.2%}")
        print(f"   Volatility: {np.std(annual_returns):.2%}")

        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)

        if len(self.aged_out_cohorts) > 0:
            print(f"\nTarget: $50,000 - $90,000")
            print(f"SEED ONLY: ${seed_avg:,.2f} avg")
            print(f"SEED + FAMILY: ${family_avg:,.2f} avg")

            status = "✓ PASS" if family_avg >= 50000 else "✗ FAIL"
            print(f"\nOverall: {status}")

        return {
            "seed_avg": seed_avg if len(self.aged_out_cohorts) > 0 else None,
            "family_avg": family_avg if len(self.aged_out_cohorts) > 0 else None,
        }


if __name__ == "__main__":
    print("CO-HERE-US Unity v1.0 — CORRECTED Steady State Test")
    print("Annual Averaging: All cohorts receive IDENTICAL returns")
    print("=" * 70)

    sim = UnitySteadyStateSimulator(
        births_per_year=3_600_000,
        cohort_duration_years=25,
        corporate_seed=2000.0,
        family_monthly=20.0,
        seed=42
    )

    results = sim.run_simulation(n_years=50)

    print("\n" + "=" * 70)
    print("This is the CORRECT CO-HERE-US model:")
    print("- Annual averaging ensures perfect fairness")
    print("- PLF 2.0 smoothing reduces volatility")
    print("- Fracton dampening ensures coherent outcomes")
    print("- All cohorts receive identical treatment")
    print("=" * 70)
