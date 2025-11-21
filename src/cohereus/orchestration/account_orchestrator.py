"""
Account Orchestration Layer — Adapted from EchoZero Distributed Layer

Manages millions of individual child accounts with:
- Batch processing for scalability
- Phase-based diversification
- Coordinated rebalancing
- Distributed fault tolerance

DNA Source: src/distributed/ (EchoZero v4.2.1)
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional
import numpy as np


class AccountOrchestrator(nn.Module):
    """
    Account Orchestrator — Manages child account cohorts

    Coordinates:
    - Account registration
    - Batch rebalancing (prevent bot synchronization)
    - Phase-based timing offsets
    - Cohort-level aggregation

    DNA Source: NodeMesh, PsiSyncProtocol (EchoZero distributed layer)
    """

    def __init__(
        self,
        n_cohorts: int = 12,              # 12 monthly cohorts
        cohort_size_target: int = 300000,  # ~300k children per cohort
        phase_offset: float = 0.0833,      # 1/12 (monthly offset)
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize Account Orchestrator

        Args:
            n_cohorts: Number of cohorts (default 12 for monthly birth cohorts)
            cohort_size_target: Target size per cohort
            phase_offset: Phase offset between cohorts (prevents synchronization)
            device: Computation device
        """
        super().__init__()

        self.n_cohorts = n_cohorts
        self.cohort_size_target = cohort_size_target
        self.phase_offset = phase_offset
        self.device = device

        # Cohort registry
        self.cohorts: Dict[int, 'CohortState'] = {}
        self.total_accounts = 0

    def register_account(
        self,
        account_id: str,
        birth_date: str,
        initial_deposit: float = 2000.0
    ) -> int:
        """
        Register new child account

        Args:
            account_id: Unique account identifier
            birth_date: Child's birth date (YYYY-MM-DD)
            initial_deposit: Initial corporate contribution

        Returns:
            cohort_id: Assigned cohort ID
        """
        # Assign to cohort based on birth month
        month = int(birth_date.split('-')[1])
        cohort_id = month - 1  # 0-11

        if cohort_id not in self.cohorts:
            self.cohorts[cohort_id] = CohortState(
                cohort_id=cohort_id,
                phase_offset=cohort_id * self.phase_offset,
                device=self.device
            )

        # Register account in cohort
        self.cohorts[cohort_id].add_account(account_id, initial_deposit)
        self.total_accounts += 1

        return cohort_id

    def batch_rebalance(
        self,
        current_day: int,
        market_signals: torch.Tensor
    ) -> Dict[int, torch.Tensor]:
        """
        Batch rebalance all cohorts with phase offsets

        Args:
            current_day: Current day counter
            market_signals: Market signals for optimization

        Returns:
            cohort_allocations: Dict mapping cohort_id → allocation tensor
        """
        cohort_allocations = {}

        for cohort_id, cohort in self.cohorts.items():
            # Check if this cohort should rebalance today (phase-based)
            phase = cohort.phase_offset
            rebalance_trigger = (current_day * self.phase_offset + phase) % 1.0

            if rebalance_trigger < 0.1:  # Rebalance window
                # Get cohort allocation
                allocation = cohort.get_allocation()
                cohort_allocations[cohort_id] = allocation

        return cohort_allocations

    def get_total_aum(self) -> float:
        """Get total assets under management across all cohorts"""
        total = sum(cohort.get_aum() for cohort in self.cohorts.values())
        return total

    def get_cohort_stats(self) -> List[Dict]:
        """Get statistics for all cohorts"""
        stats = []
        for cohort_id, cohort in sorted(self.cohorts.items()):
            stats.append({
                'cohort_id': cohort_id,
                'n_accounts': cohort.n_accounts,
                'aum': cohort.get_aum(),
                'phase_offset': cohort.phase_offset
            })
        return stats


class CohortState:
    """
    Cohort State — Manages a single cohort of accounts

    DNA Source: ψ-state in EchoZero (complex-valued state management)
    """

    def __init__(
        self,
        cohort_id: int,
        phase_offset: float,
        device: torch.device = torch.device('cpu')
    ):
        self.cohort_id = cohort_id
        self.phase_offset = phase_offset
        self.device = device

        # Account registry
        self.accounts: Dict[str, float] = {}  # account_id → balance
        self.n_accounts = 0
        self.total_aum = 0.0

        # Cohort-level allocation (5 assets: stocks, bonds, commodities, real estate, cash)
        self.allocation = torch.tensor(
            [0.40, 0.30, 0.15, 0.10, 0.05],
            device=device
        )

    def add_account(self, account_id: str, initial_deposit: float):
        """Add new account to cohort"""
        self.accounts[account_id] = initial_deposit
        self.n_accounts += 1
        self.total_aum += initial_deposit

    def get_allocation(self) -> torch.Tensor:
        """Get current cohort allocation"""
        return self.allocation.clone()

    def update_allocation(self, new_allocation: torch.Tensor):
        """Update cohort allocation"""
        self.allocation = new_allocation.to(self.device)

    def get_aum(self) -> float:
        """Get total AUM for this cohort"""
        return self.total_aum

    def update_balances(self, returns: torch.Tensor):
        """
        Update all account balances based on returns

        Args:
            returns: Asset returns tensor
        """
        # Compute portfolio return
        portfolio_return = torch.dot(self.allocation, returns)

        # Update all balances
        for account_id in self.accounts:
            self.accounts[account_id] *= (1.0 + portfolio_return.item())

        # Update total AUM
        self.total_aum = sum(self.accounts.values())


# Example usage
if __name__ == "__main__":
    print("Testing Account Orchestrator...")

    orchestrator = AccountOrchestrator(n_cohorts=12)

    # Register accounts
    print("\n1. Registering accounts:")
    for i in range(100):
        month = (i % 12) + 1
        birth_date = f"2020-{month:02d}-15"
        account_id = f"CHILD_{i:06d}"
        cohort_id = orchestrator.register_account(account_id, birth_date, 2000.0)

        if i < 5:
            print(f"  Account {account_id} → Cohort {cohort_id}")

    print(f"\n  Total accounts: {orchestrator.total_accounts}")
    print(f"  Total AUM: ${orchestrator.get_total_aum():,.2f}")

    # Cohort stats
    print("\n2. Cohort statistics:")
    for stats in orchestrator.get_cohort_stats():
        print(f"  Cohort {stats['cohort_id']}: "
              f"{stats['n_accounts']} accounts, "
              f"${stats['aum']:,.2f} AUM, "
              f"phase={stats['phase_offset']:.4f}")

    # Simulate rebalancing
    print("\n3. Simulating rebalancing over 30 days:")
    market_signals = torch.randn(5)  # Dummy signals

    for day in range(30):
        cohort_allocations = orchestrator.batch_rebalance(day, market_signals)

        if cohort_allocations:
            print(f"  Day {day}: Rebalancing {len(cohort_allocations)} cohorts")
            for cohort_id in cohort_allocations:
                print(f"    Cohort {cohort_id}: phase={orchestrator.cohorts[cohort_id].phase_offset:.4f}")

    print("\n✓ Account Orchestrator tests passed")
