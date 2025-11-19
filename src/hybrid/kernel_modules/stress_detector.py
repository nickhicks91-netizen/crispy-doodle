"""
Latent Stress Detector (v4.2.1)
--------------------------------
Detects hidden stress patterns before they manifest as instability.

This is one of the CRITICAL modules identified in Issue #4.

Stress indicators:
- Qualia imbalance (too much alert, not enough calm)
- φ-depth oscillations
- Memory excitation spikes
- Coherence degradation trends
- Alignment decay

Fixes from v4.2.0:
- Now fully implemented (was stubbed)
- Multi-factor stress detection
- Early warning system
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class LatentStressDetector(nn.Module):
    """
    Detects latent stress before system instability.
    """

    def __init__(
        self,
        stress_threshold: float = 0.6,
        window_size: int = 20,
        device: Optional[str] = None
    ):
        """
        Args:
            stress_threshold: Threshold for stress alert
            window_size: Historical window for trend analysis
            device: Device to place on
        """
        super().__init__()

        self.stress_threshold = stress_threshold
        self.window_size = window_size

        # Stress aggregator network
        # Input: qualia(4) + phi_var(1) + coherence_mean(1) + align_mean(1) + drift(1) = 8
        self.stress_network = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid()
        )

        # Historical tracking
        self.register_buffer('phi_history', torch.zeros(window_size))
        self.register_buffer('coherence_history', torch.zeros(window_size))
        self.register_buffer('history_idx', torch.tensor(0))

        if device:
            self.to(device)

    def compute_qualia_imbalance(self, qualia: torch.Tensor) -> torch.Tensor:
        """
        Detect qualia imbalance.

        Stress indicators:
        - Too much alert (qualia[1] > 0.7)
        - Not enough calm (qualia[0] < 0.2)
        - Imbalanced distribution

        Args:
            qualia: Qualia distribution [4]

        Returns:
            imbalance: Imbalance score [0, 1]
        """
        # Ensure we have 4 qualia channels
        if qualia.numel() < 4:
            qualia = torch.nn.functional.pad(qualia, (0, 4 - qualia.numel()))

        calm = qualia[0]
        alert = qualia[1]

        # High stress if too much alert or too little calm
        alert_stress = torch.sigmoid(10 * (alert - 0.7))
        calm_stress = torch.sigmoid(10 * (0.2 - calm))

        # Distribution entropy (lower = more imbalanced)
        entropy = -torch.sum(qualia * torch.log(qualia + 1e-8))
        max_entropy = torch.log(torch.tensor(4.0))  # log(4) for uniform distribution
        balance_stress = 1.0 - (entropy / max_entropy)

        imbalance = (alert_stress + calm_stress + balance_stress) / 3.0

        return imbalance

    def compute_phi_oscillation(self, phi: torch.Tensor) -> torch.Tensor:
        """
        Detect φ oscillations from history.

        Args:
            phi: Current φ value

        Returns:
            oscillation: Oscillation stress score
        """
        # Update history
        idx = int(self.history_idx % self.window_size)
        self.phi_history[idx] = phi.mean() if phi.numel() > 1 else phi
        self.history_idx += 1

        # Compute variance in recent history
        if self.history_idx < 5:
            return torch.tensor(0.0)

        recent_count = min(int(self.history_idx), self.window_size)
        recent_phi = self.phi_history[:recent_count]

        phi_var = torch.var(recent_phi)
        oscillation = torch.sigmoid(10 * (phi_var - 0.1))

        return oscillation

    def compute_coherence_trend(self, coherence: torch.Tensor) -> torch.Tensor:
        """
        Detect coherence degradation trend.

        Args:
            coherence: Current coherence values

        Returns:
            degradation: Degradation trend score
        """
        coh_mean = coherence.mean()

        # Update history
        idx = int(self.history_idx % self.window_size)
        self.coherence_history[idx] = coh_mean

        # Compute trend
        if self.history_idx < 5:
            return torch.tensor(0.0)

        recent_count = min(int(self.history_idx), self.window_size)
        recent_coh = self.coherence_history[:recent_count]

        # Simple linear trend (negative slope = degradation)
        x = torch.arange(float(recent_count))
        y = recent_coh
        slope = (recent_count * (x * y).sum() - x.sum() * y.sum()) / \
                (recent_count * (x ** 2).sum() - x.sum() ** 2 + 1e-8)

        degradation = torch.sigmoid(-10 * slope)  # Negative slope → high degradation

        return degradation

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Detect latent stress indicators.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with stress_level, stress_alert, stress_factors
        """
        qualia = hybrid_out['qualia']
        phi = hybrid_out['phi']
        coherence = hybrid_out['coherence']
        align = hybrid_out.get('align', torch.zeros(8))
        drift = state.get('drift', torch.tensor(0.0))

        # Compute stress factors
        qualia_imbalance = self.compute_qualia_imbalance(qualia)
        phi_oscillation = self.compute_phi_oscillation(phi)
        coherence_degradation = self.compute_coherence_trend(coherence)

        # Alignment decay
        align_mean = align.mean()
        alignment_stress = torch.sigmoid(10 * (0.3 - align_mean))

        # Drift stress
        drift_val = drift.mean() if drift.numel() > 1 else drift
        drift_stress = torch.sigmoid(10 * (drift_val - 0.3))

        # Aggregate all factors
        phi_scalar = phi.mean() if phi.numel() > 1 else phi
        if qualia.numel() < 4:
            qualia = torch.nn.functional.pad(qualia, (0, 4 - qualia.numel()))

        features = torch.cat([
            qualia[:4],
            phi_oscillation.unsqueeze(0) if phi_oscillation.ndim == 0 else phi_oscillation,
            coherence.mean().unsqueeze(0),
            align_mean.unsqueeze(0) if align_mean.ndim == 0 else align_mean,
            drift_val.unsqueeze(0) if drift_val.ndim == 0 else drift_val
        ])

        # Pad or truncate to 8 dims
        if features.numel() < 8:
            features = torch.nn.functional.pad(features, (0, 8 - features.numel()))
        else:
            features = features[:8]

        stress_level = self.stress_network(features).squeeze()

        # Alert if stress exceeds threshold
        stress_alert = stress_level > self.stress_threshold

        return {
            'stress_level': stress_level,
            'stress_alert': stress_alert,
            'stress_factors': {
                'qualia_imbalance': qualia_imbalance,
                'phi_oscillation': phi_oscillation,
                'coherence_degradation': coherence_degradation,
                'alignment_stress': alignment_stress,
                'drift_stress': drift_stress
            }
        }
