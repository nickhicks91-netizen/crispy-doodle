"""
CO-HERE-US Unity v1.0 - System Orchestrator

Manages the entire CO-HERE-US system at national scale.
Implements annual averaging to ensure perfect fairness across all cohorts.
"""

from typing import List, Dict, Tuple
import numpy as np

from .config import (
    BIRTHS_PER_YEAR,
    COHORT_DURATION_YEARS,
    ANNUAL_AVERAGING_ENABLED,
)
from .market_engine import MarketEngine
from .plf import PLFController
from .fracton import FractonController
from .portfolio import Cohort


class UnityOrchestrator:
    """
    CO-HERE-US Unity v1.0 Orchestrator.

    Manages the entire system:
    - Generates market returns with multi-scale averaging
    - Applies PLF smoothing (35%)
    - Applies Fracton dampening (5% negative only)
    - Distributes IDENTICAL returns to all cohorts (annual averaging)
    - Manages cohort lifecycle (birth to age 25 distribution)
    """

    def __init__(
        self,
        births_per_year: int = BIRTHS_PER_YEAR,
        cohort_duration: int = COHORT_DURATION_YEARS,
        random_seed: int = None,
    ):
        """
        Initialize Unity orchestrator.

        Args:
            births_per_year: Number of children born per year
            cohort_duration: Years before distribution (age 25)
            random_seed: Random seed for reproducibility
        """
        self.births_per_year = births_per_year
        self.cohort_duration = cohort_duration

        # Core engines
        self.market = MarketEngine(seed=random_seed)
        self.plf = PLFController()
        self.fracton = FractonController()

        # Cohort tracking
        self.active_cohorts: List[Cohort] = []
        self.distributed_cohorts: List[Cohort] = []
        self.current_year = 0

    def initialize_year_zero(self):
        """Create the first cohort (year 0)."""
        cohort = Cohort.create_new(
            birth_year=self.current_year,
            cohort_id=0,
            num_children=self.births_per_year,
        )
        self.active_cohorts.append(cohort)

    def run_simulation(self, n_years: int) -> Dict:
        """
        Run multi-year simulation.

        Args:
            n_years: Number of years to simulate

        Returns:
            Dict: Simulation results
        """
        # Pre-generate all returns for the simulation
        raw_returns = self.market.generate_sequence(n_years)
        raw_returns = np.array(raw_returns)

        # Apply PLF smoothing
        smoothed_returns = self.plf.smooth(raw_returns)

        # Apply Fracton dampening (negative only)
        final_returns = self.fracton.dampen(smoothed_returns)

        # Initialize first cohort
        if not self.active_cohorts:
            self.initialize_year_zero()

        # Run each year
        for year in range(n_years):
            annual_return = final_returns[year]
            self._run_year(annual_return)
            self.current_year += 1

        # Collect results
        return self._compile_results()

    def _run_year(self, annual_return: float):
        """
        Run one year of the simulation.

        Args:
            annual_return: The return to apply to ALL cohorts
        """
        # Add monthly family contributions for all active cohorts
        for cohort in self.active_cohorts:
            if not cohort.aged_out:
                cohort.add_monthly_contributions()

        # Apply IDENTICAL return to ALL cohorts (annual averaging)
        if ANNUAL_AVERAGING_ENABLED:
            for cohort in self.active_cohorts:
                if not cohort.aged_out:
                    cohort.apply_return(annual_return)
        else:
            # If annual averaging disabled, each cohort gets independent returns
            # (This should never be used in production)
            for cohort in self.active_cohorts:
                if not cohort.aged_out:
                    independent_return = self.market.generate_year()
                    cohort.apply_return(independent_return)

        # Age all cohorts
        for cohort in self.active_cohorts:
            if not cohort.aged_out:
                cohort.age_one_year()

        # Distribute cohorts that reached age 25
        aged_out = []
        for cohort in self.active_cohorts:
            if cohort.age_years >= self.cohort_duration and not cohort.aged_out:
                cohort.aged_out = True
                self.distributed_cohorts.append(cohort)
                aged_out.append(cohort)

        # Remove aged-out cohorts from active list
        self.active_cohorts = [c for c in self.active_cohorts if not c.aged_out]

        # Add new cohort (newborns)
        new_cohort_id = len(self.active_cohorts) + len(self.distributed_cohorts)
        new_cohort = Cohort.create_new(
            birth_year=self.current_year + 1,
            cohort_id=new_cohort_id,
            num_children=self.births_per_year,
        )
        self.active_cohorts.append(new_cohort)

    def _compile_results(self) -> Dict:
        """Compile simulation results."""
        if not self.distributed_cohorts:
            return {
                "years_simulated": self.current_year,
                "active_cohorts": len(self.active_cohorts),
                "distributed_cohorts": 0,
                "outcomes": {},
            }

        # Calculate outcomes for distributed cohorts
        seed_outcomes = [c.seed_only_per_child() for c in self.distributed_cohorts]
        total_outcomes = [c.total_per_child() for c in self.distributed_cohorts]

        return {
            "years_simulated": self.current_year,
            "active_cohorts": len(self.active_cohorts),
            "distributed_cohorts": len(self.distributed_cohorts),
            "active_children": sum(c.num_children for c in self.active_cohorts),
            "outcomes": {
                "seed_only": {
                    "mean": np.mean(seed_outcomes),
                    "median": np.median(seed_outcomes),
                    "min": np.min(seed_outcomes),
                    "max": np.max(seed_outcomes),
                    "std": np.std(seed_outcomes),
                },
                "seed_family": {
                    "mean": np.mean(total_outcomes),
                    "median": np.median(total_outcomes),
                    "min": np.min(total_outcomes),
                    "max": np.max(total_outcomes),
                    "std": np.std(total_outcomes),
                },
            },
        }

    def get_active_children(self) -> int:
        """Get total number of active children in system."""
        return sum(c.num_children for c in self.active_cohorts)

    def get_steady_state_capacity(self) -> int:
        """Get theoretical steady state capacity."""
        return self.births_per_year * self.cohort_duration

    def __repr__(self) -> str:
        return (
            f"UnityOrchestrator("
            f"year={self.current_year}, "
            f"active={len(self.active_cohorts)} cohorts, "
            f"distributed={len(self.distributed_cohorts)} cohorts)"
        )
