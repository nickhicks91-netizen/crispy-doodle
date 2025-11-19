"""
Scenario Generator (v4.2.1)
----------------------------
Generates hypothetical scenarios for internal simulation and planning.

Scenarios include:
- "What if ψ diverges?"
- "What if coherence drops?"
- "What if input changes dramatically?"

Used for:
- Risk assessment
- Planning
- Stress testing
- Counterfactual reasoning

Fixes from v4.2.0:
- Proper state management
- Efficient scenario generation
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Dict, Optional, List


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class ScenarioGenerator(nn.Module):
    """
    Internal scenario simulation for planning.
    """

    def __init__(
        self,
        N: Optional[int] = None,
        scenario_dim: Optional[int] = None,
        num_scenarios: int = 5,
        device: Optional[str] = None
    ):
        """
        Args:
            N: Number of ψ nodes
            scenario_dim: Scenario representation dimension
            num_scenarios: Number of scenarios to generate
            device: Device to place on
        """
        super().__init__()

        self.N = N or DIMS['N']
        self.scenario_dim = scenario_dim or DIMS.get('scenario_dim', 24)
        self.num_scenarios = num_scenarios

        # Scenario encoder: current state → base scenario
        # Input: psi_real(N) + qualia(4) + phi(1) + coherence_mean(1)
        input_dim = self.N + 6
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, self.scenario_dim),
            nn.Tanh()
        )

        # Scenario perturbator: base → perturbed scenarios
        self.perturbators = nn.ModuleList([
            nn.Linear(self.scenario_dim, self.scenario_dim)
            for _ in range(num_scenarios)
        ])

        # Outcome predictor: scenario → expected φ
        self.outcome_predictor = nn.Sequential(
            nn.Linear(self.scenario_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

        if device:
            self.to(device)

    def encode_current_state(self, hybrid_out: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Encode current state as base scenario.

        Args:
            hybrid_out: Hybrid forward output

        Returns:
            base_scenario: Base scenario representation
        """
        psi = hybrid_out['psi']
        qualia = hybrid_out['qualia']
        phi = hybrid_out['phi']
        coherence = hybrid_out['coherence']

        # Extract features
        psi_real = torch.real(psi)
        if psi_real.ndim > 1:
            psi_real = psi_real[0]  # Take first batch element

        phi_val = phi.mean() if phi.numel() > 1 else phi
        coh_val = coherence.mean()

        # Pad qualia
        if qualia.numel() < 4:
            qualia = torch.nn.functional.pad(qualia, (0, 4 - qualia.numel()))
        elif qualia.ndim > 1:
            qualia = qualia[0, :4]

        # Concatenate
        features = torch.cat([
            psi_real,
            qualia[:4],
            phi_val.unsqueeze(0) if phi_val.ndim == 0 else phi_val,
            coh_val.unsqueeze(0) if coh_val.ndim == 0 else coh_val
        ])

        # Encode
        base_scenario = self.encoder(features)

        return base_scenario

    def generate_scenarios(self, base_scenario: torch.Tensor) -> List[torch.Tensor]:
        """
        Generate perturbed scenarios.

        Args:
            base_scenario: Base scenario

        Returns:
            scenarios: List of perturbed scenarios
        """
        scenarios = []

        for perturbator in self.perturbators:
            perturbed = perturbator(base_scenario)
            perturbed = torch.tanh(perturbed)  # Bound perturbations
            scenarios.append(perturbed)

        return scenarios

    def predict_outcomes(self, scenarios: List[torch.Tensor]) -> torch.Tensor:
        """
        Predict outcomes for each scenario.

        Args:
            scenarios: List of scenarios

        Returns:
            outcomes: Predicted φ for each scenario [num_scenarios]
        """
        outcomes = []

        for scenario in scenarios:
            outcome = self.outcome_predictor(scenario)
            outcomes.append(outcome.squeeze())

        return torch.stack(outcomes)

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Generate and evaluate scenarios.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with scenarios, outcomes, best_scenario, worst_scenario
        """
        # Encode current state
        base_scenario = self.encode_current_state(hybrid_out)

        # Generate scenarios
        scenarios = self.generate_scenarios(base_scenario)

        # Predict outcomes
        outcomes = self.predict_outcomes(scenarios)

        # Find best and worst scenarios
        best_idx = torch.argmax(outcomes)
        worst_idx = torch.argmin(outcomes)

        return {
            'base_scenario': base_scenario,
            'num_scenarios': len(scenarios),
            'scenario_outcomes': outcomes,
            'best_outcome': outcomes[best_idx],
            'worst_outcome': outcomes[worst_idx],
            'outcome_variance': torch.var(outcomes)
        }
