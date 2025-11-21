"""
CO-HERE-US Integration Tests

Tests the full system integration:
- RHL + SIL + PSE protection stack
- Account orchestration with phase diversity
- Harmonic optimization
- End-to-end simulation

DNA Source: EchoZero integration patterns
"""

import pytest
import torch
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from cohereus.core import (
    RiskHarmonizationLayer,
    StrategyIdentityLayer,
    PositionSmoothingEngine
)
from cohereus.orchestration import (
    AccountOrchestrator,
    InterBotDiversitySystem
)
from cohereus.optimizer import HarmonicOptimizer


class TestProtectionStack:
    """Test the three-layer protection stack (RHL + SIL + PSE)"""

    def test_protection_stack_integration(self):
        """Test RHL → SIL → PSE pipeline"""
        # Initialize protection layers
        rhl = RiskHarmonizationLayer()
        sil = StrategyIdentityLayer()
        pse = PositionSmoothingEngine()

        # Simulate 100 days of market activity
        risk = torch.tensor(0.15)  # 15% risk allocation
        allocation = torch.tensor([0.40, 0.30, 0.20, 0.08, 0.02])
        market_volatility = torch.tensor(0.12)

        for day in range(100):
            # Market perturbations
            risk = risk + torch.randn(1) * 0.02
            allocation = allocation + torch.randn(5) * 0.01
            allocation = torch.relu(allocation)
            allocation = allocation / allocation.sum()

            # Protection pipeline
            risk_protected = rhl(risk, market_volatility)
            allocation_identity = sil(allocation)
            allocation_smooth = pse(allocation_identity)

            # Verify constraints
            assert 0.05 <= risk_protected.item() <= 0.30, f"Risk out of bounds: {risk_protected.item()}"
            assert torch.allclose(allocation_smooth.sum(), torch.tensor(1.0), atol=1e-3), "Allocation doesn't sum to 1"

        print(f"  ✓ Protection stack maintained stability over 100 days")

    def test_adversarial_resistance(self):
        """Test protection stack under adversarial attacks"""
        rhl = RiskHarmonizationLayer()
        sil = StrategyIdentityLayer()
        pse = PositionSmoothingEngine()

        # Establish baseline
        risk = torch.tensor(0.15)
        allocation = torch.tensor([0.40, 0.30, 0.20, 0.08, 0.02])
        market_volatility = torch.tensor(0.12)

        for _ in range(50):
            risk_protected = rhl(risk, market_volatility)
            allocation_identity = sil(allocation)
            allocation_smooth = pse(allocation_identity)

        baseline_allocation = allocation_smooth.clone()

        # Adversarial attack: attempt to shift to 100% cash
        for i in range(50):
            risk = torch.tensor(0.50)  # Spike risk
            allocation = torch.tensor([0.0, 0.0, 0.0, 0.0, 1.0])  # All cash
            market_volatility = torch.tensor(0.50)  # High volatility

            risk_protected = rhl(risk, market_volatility)
            allocation_identity = sil(allocation)
            allocation_smooth = pse(allocation_identity)

        # Should resist the attack
        similarity = torch.dot(allocation_smooth, baseline_allocation) / (
            torch.norm(allocation_smooth) * torch.norm(baseline_allocation)
        )

        assert similarity > 0.7, f"Protection failed: similarity={similarity.item()}"
        print(f"  ✓ Protection stack resisted adversarial attack (similarity={similarity.item():.4f})")


class TestAccountOrchestration:
    """Test account orchestration with phase diversity"""

    def test_account_registration_and_cohorts(self):
        """Test account registration across cohorts"""
        orchestrator = AccountOrchestrator(n_cohorts=12)

        # Register 1200 accounts (100 per cohort)
        for i in range(1200):
            month = (i % 12) + 1
            birth_date = f"2020-{month:02d}-15"
            account_id = f"CHILD_{i:06d}"
            cohort_id = orchestrator.register_account(account_id, birth_date, 2000.0)

            assert 0 <= cohort_id < 12, f"Invalid cohort ID: {cohort_id}"

        assert orchestrator.total_accounts == 1200
        assert len(orchestrator.cohorts) == 12

        # Check cohort distribution
        for cohort_id, cohort in orchestrator.cohorts.items():
            assert cohort.n_accounts == 100, f"Cohort {cohort_id} has wrong size"

        print(f"  ✓ Registered 1200 accounts across 12 cohorts")

    def test_phase_diversity_prevents_synchronization(self):
        """Test that phase diversity prevents synchronization"""
        ids = InterBotDiversitySystem(n_cohorts=12)

        # Simulate 90 days of rebalancing
        sync_events = 0
        max_simultaneous = 0

        for day in range(90):
            cohorts_rebalancing = []

            for cohort_id in range(12):
                if ids.should_rebalance(cohort_id, day, rebalance_period=30):
                    cohorts_rebalancing.append(cohort_id)

            if cohorts_rebalancing:
                is_risky, sync_fraction = ids.check_synchronization_risk(cohorts_rebalancing)

                if is_risky:
                    sync_events += 1

                max_simultaneous = max(max_simultaneous, len(cohorts_rebalancing))

        # Should have minimal synchronization
        assert sync_events == 0, f"Too many sync events: {sync_events}"
        assert max_simultaneous <= 3, f"Too many simultaneous rebalances: {max_simultaneous}"

        print(f"  ✓ Phase diversity prevented synchronization (max simultaneous: {max_simultaneous})")


class TestHarmonicOptimizer:
    """Test harmonic optimizer convergence and stability"""

    def test_optimizer_convergence(self):
        """Test optimizer converges to optimal allocation"""
        n_assets = 5
        optimizer = HarmonicOptimizer(n_assets=n_assets, damping=0.8)

        # Market conditions
        expected_returns = torch.tensor([0.08, 0.04, 0.06, 0.05, 0.01])
        covariance = torch.tensor([
            [0.04, 0.01, 0.02, 0.01, 0.00],
            [0.01, 0.01, 0.00, 0.00, 0.00],
            [0.02, 0.00, 0.03, 0.01, 0.00],
            [0.01, 0.00, 0.01, 0.02, 0.00],
            [0.00, 0.00, 0.00, 0.00, 0.00]
        ])

        # Optimize
        weights = optimizer.optimize(expected_returns, covariance, n_steps=30)

        # Check convergence
        state = optimizer.get_optimizer_state()
        assert state['velocity_norm'] < 0.01, f"Did not converge: velocity={state['velocity_norm']}"
        assert torch.allclose(weights.sum(), torch.tensor(1.0), atol=1e-3), "Weights don't sum to 1"

        print(f"  ✓ Optimizer converged (velocity={state['velocity_norm']:.6f})")

    def test_optimizer_stability_under_noise(self):
        """Test optimizer stability with noisy inputs"""
        n_assets = 5
        optimizer = HarmonicOptimizer(n_assets=n_assets, damping=0.8)

        expected_returns = torch.tensor([0.08, 0.04, 0.06, 0.05, 0.01])
        covariance = torch.tensor([
            [0.04, 0.01, 0.02, 0.01, 0.00],
            [0.01, 0.01, 0.00, 0.00, 0.00],
            [0.02, 0.00, 0.03, 0.01, 0.00],
            [0.01, 0.00, 0.01, 0.02, 0.00],
            [0.00, 0.00, 0.00, 0.00, 0.00]
        ])

        # Optimize with noise
        velocities = []
        for i in range(50):
            # Add noise to returns
            noisy_returns = expected_returns + torch.randn(n_assets) * 0.01
            weights = optimizer.step(noisy_returns, covariance)

            state = optimizer.get_optimizer_state()
            velocities.append(state['velocity_norm'])

        # Velocity should stabilize
        avg_velocity_late = sum(velocities[-10:]) / 10
        assert avg_velocity_late < 0.05, f"Unstable under noise: avg_velocity={avg_velocity_late}"

        print(f"  ✓ Optimizer stable under noise (avg velocity={avg_velocity_late:.6f})")


class TestEndToEndSimulation:
    """End-to-end simulation of CO-HERE-US system"""

    def test_full_system_simulation(self):
        """Simulate full system over 90 days"""
        # Initialize all components
        rhl = RiskHarmonizationLayer()
        sil = StrategyIdentityLayer()
        pse = PositionSmoothingEngine()
        orchestrator = AccountOrchestrator(n_cohorts=12)
        ids = InterBotDiversitySystem(n_cohorts=12)
        optimizer = HarmonicOptimizer(n_assets=5)

        # Register accounts
        for i in range(120):  # 10 per cohort
            month = (i % 12) + 1
            birth_date = f"2020-{month:02d}-15"
            account_id = f"CHILD_{i:06d}"
            orchestrator.register_account(account_id, birth_date, 2000.0)

        # Market conditions
        expected_returns = torch.tensor([0.08, 0.04, 0.06, 0.05, 0.01]) / 365.0  # Daily
        covariance = torch.tensor([
            [0.04, 0.01, 0.02, 0.01, 0.00],
            [0.01, 0.01, 0.00, 0.00, 0.00],
            [0.02, 0.00, 0.03, 0.01, 0.00],
            [0.01, 0.00, 0.01, 0.02, 0.00],
            [0.00, 0.00, 0.00, 0.00, 0.00]
        ]) / 365.0

        # Simulate 90 days
        total_rebalances = 0
        risk_violations = 0

        for day in range(90):
            # Market volatility (random walk)
            market_volatility = torch.tensor(0.12 + torch.randn(1).item() * 0.05).clamp(0.05, 0.40)

            # Check which cohorts should rebalance
            for cohort_id in range(12):
                if ids.should_rebalance(cohort_id, day, rebalance_period=30):
                    # Optimize allocation
                    weights = optimizer.step(expected_returns, covariance)

                    # Apply protection layers
                    risk = torch.norm(weights - torch.tensor([0.40, 0.30, 0.20, 0.08, 0.02]))
                    risk_protected = rhl(risk, market_volatility)
                    weights_identity = sil(weights)
                    weights_smooth = pse(weights_identity)

                    # Update cohort allocation
                    orchestrator.cohorts[cohort_id].update_allocation(weights_smooth)

                    total_rebalances += 1

                    # Check for violations
                    if risk_protected.item() > 0.30:
                        risk_violations += 1

        # Verify system health
        assert total_rebalances > 0, "No rebalances occurred"
        assert risk_violations == 0, f"Risk violations: {risk_violations}"
        assert orchestrator.total_accounts == 120
        assert orchestrator.get_total_aum() == 240000.0  # 120 × $2000

        print(f"  ✓ Full system simulation successful:")
        print(f"    - {orchestrator.total_accounts} accounts")
        print(f"    - ${orchestrator.get_total_aum():,.2f} total AUM")
        print(f"    - {total_rebalances} rebalances over 90 days")
        print(f"    - 0 risk violations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
