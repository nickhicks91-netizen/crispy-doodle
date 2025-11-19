"""
Meta-Stability Analyzer (v4.2.1)
---------------------------------
Analyzes system-wide stability across multiple dimensions.

Stability dimensions:
- ψ-state stability (drift, oscillations)
- Memory stability (variance, coherence)
- φ-depth stability (trends, fluctuations)
- Coherence stability (degradation, recovery)
- Identity stability (consistency over time)

Generates:
- Stability index [0, 1]
- Stability alerts
- Recommended interventions

Fixes from v4.2.0:
- Proper state management
- Multi-dimensional stability analysis
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class MetaStabilityAnalyzer(nn.Module):
    """
    System-wide stability analysis and monitoring.
    """

    def __init__(
        self,
        stability_threshold: float = 0.4,
        device: Optional[str] = None
    ):
        """
        Args:
            stability_threshold: Minimum acceptable stability
            device: Device to place on
        """
        super().__init__()

        self.stability_threshold = stability_threshold

        # Stability aggregator
        # Input: psi_stability(1) + memory_stability(1) + phi_stability(1) +
        #        coherence_stability(1) + identity_stability(1) = 5
        self.aggregator = nn.Sequential(
            nn.Linear(5, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

        # Intervention recommender
        self.recommender = nn.Sequential(
            nn.Linear(1, 8),
            nn.ReLU(),
            nn.Linear(8, 4),  # 4 intervention types
            nn.Sigmoid()
        )

        # Historical stability tracking
        self.register_buffer('stability_history', torch.zeros(100))
        self.register_buffer('history_idx', torch.tensor(0))

        if device:
            self.to(device)

    def compute_psi_stability(self, drift: torch.Tensor) -> torch.Tensor:
        """
        Compute ψ-state stability.

        Args:
            drift: Current drift value

        Returns:
            stability: ψ stability [0, 1] (higher = more stable)
        """
        drift_val = drift.mean() if drift.numel() > 1 else drift
        # Stability is inverse of drift
        stability = torch.sigmoid(-10 * (drift_val - 0.3))
        return stability

    def compute_memory_stability(self, memory: torch.Tensor) -> torch.Tensor:
        """
        Compute memory stability.

        Args:
            memory: Memory vector

        Returns:
            stability: Memory stability
        """
        # Low variance = high stability
        variance = torch.var(memory)
        stability = torch.sigmoid(-5 * (variance - 0.5))
        return stability

    def compute_phi_stability(self, phi: torch.Tensor) -> torch.Tensor:
        """
        Compute φ-depth stability from history.

        Args:
            phi: Current φ value

        Returns:
            stability: φ stability
        """
        phi_val = phi.mean() if phi.numel() > 1 else phi

        # Update history
        idx = int(self.history_idx % 100)
        self.stability_history[idx] = phi_val
        self.history_idx += 1

        # Compute stability from variance
        if self.history_idx < 10:
            return torch.tensor(0.5)  # Default

        recent_count = min(int(self.history_idx), 100)
        recent = self.stability_history[:recent_count]
        variance = torch.var(recent)

        stability = torch.sigmoid(-10 * (variance - 0.1))
        return stability

    def compute_coherence_stability(self, coherence: torch.Tensor) -> torch.Tensor:
        """
        Compute coherence stability.

        Args:
            coherence: Coherence values

        Returns:
            stability: Coherence stability
        """
        coh_mean = coherence.mean()
        coh_std = coherence.std()

        # High mean + low std = stable
        stability = torch.sigmoid(10 * (coh_mean - 0.5)) * torch.sigmoid(-5 * (coh_std - 0.2))
        return stability

    def aggregate_stability(
        self,
        psi_stab: torch.Tensor,
        mem_stab: torch.Tensor,
        phi_stab: torch.Tensor,
        coh_stab: torch.Tensor,
        id_stab: torch.Tensor
    ) -> torch.Tensor:
        """
        Aggregate stability metrics.

        Args:
            psi_stab: ψ stability
            mem_stab: Memory stability
            phi_stab: φ stability
            coh_stab: Coherence stability
            id_stab: Identity stability

        Returns:
            meta_stability: Aggregated stability index
        """
        features = torch.cat([
            psi_stab.unsqueeze(0) if psi_stab.ndim == 0 else psi_stab,
            mem_stab.unsqueeze(0) if mem_stab.ndim == 0 else mem_stab,
            phi_stab.unsqueeze(0) if phi_stab.ndim == 0 else phi_stab,
            coh_stab.unsqueeze(0) if coh_stab.ndim == 0 else coh_stab,
            id_stab.unsqueeze(0) if id_stab.ndim == 0 else id_stab
        ])

        meta_stability = self.aggregator(features)
        return meta_stability.squeeze()

    def recommend_interventions(self, stability: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Recommend interventions based on stability.

        Args:
            stability: Meta-stability value

        Returns:
            interventions: Recommended intervention strengths
        """
        stability_deficit = torch.relu(self.stability_threshold - stability)

        if float(stability_deficit) < 0.01:
            # System stable, no interventions
            return {
                'dampen_psi': torch.tensor(0.0),
                'consolidate_memory': torch.tensor(0.0),
                'realign_goals': torch.tensor(0.0),
                'trigger_sleep': torch.tensor(0.0)
            }

        # Generate intervention recommendations
        interventions = self.recommender(stability.unsqueeze(0)).squeeze()

        return {
            'dampen_psi': interventions[0],
            'consolidate_memory': interventions[1],
            'realign_goals': interventions[2],
            'trigger_sleep': interventions[3]
        }

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Analyze system stability.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with stability metrics and recommendations
        """
        # Compute component stabilities
        drift = state.get('drift', torch.tensor(0.0))
        psi_stability = self.compute_psi_stability(drift)

        memory = hybrid_out['memory']
        memory_stability = self.compute_memory_stability(memory)

        phi = hybrid_out['phi']
        phi_stability = self.compute_phi_stability(phi)

        coherence = hybrid_out['coherence']
        coherence_stability = self.compute_coherence_stability(coherence)

        identity_stability = state.get('identity_stability', torch.tensor(0.5))

        # Aggregate
        meta_stability = self.aggregate_stability(
            psi_stability,
            memory_stability,
            phi_stability,
            coherence_stability,
            identity_stability
        )

        # Recommend interventions
        interventions = self.recommend_interventions(meta_stability)

        # Alert if stability too low
        stability_alert = meta_stability < self.stability_threshold

        return {
            'meta_stability': meta_stability,
            'stability_alert': stability_alert,
            'component_stabilities': {
                'psi': psi_stability,
                'memory': memory_stability,
                'phi': phi_stability,
                'coherence': coherence_stability,
                'identity': identity_stability
            },
            'interventions': interventions
        }
