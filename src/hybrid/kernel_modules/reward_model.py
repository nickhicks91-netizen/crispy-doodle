"""
Harmonized Reward Model (v4.2.1)
---------------------------------
Non-RL reward shaping based on harmonic principles.

This is NOT reinforcement learning. This is harmonic reward shaping:
- Rewards high φ-depth
- Rewards coherence
- Rewards goal alignment
- Rewards stability
- Penalizes drift
- Penalizes stress

Used for:
- Curriculum adaptation
- Tool policy shaping
- Behavior guidance

Fixes from v4.2.0:
- Proper state management
- Multi-factor reward computation
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class HarmonicRewardModel(nn.Module):
    """
    Harmonic reward shaping (non-RL).
    """

    def __init__(
        self,
        phi_weight: float = 0.3,
        coherence_weight: float = 0.2,
        alignment_weight: float = 0.2,
        stability_weight: float = 0.2,
        stress_penalty: float = 0.1,
        device: Optional[str] = None
    ):
        """
        Args:
            phi_weight: Weight for φ-depth reward
            coherence_weight: Weight for coherence reward
            alignment_weight: Weight for alignment reward
            stability_weight: Weight for stability reward
            stress_penalty: Penalty weight for stress
            device: Device to place on
        """
        super().__init__()

        self.phi_weight = phi_weight
        self.coherence_weight = coherence_weight
        self.alignment_weight = alignment_weight
        self.stability_weight = stability_weight
        self.stress_penalty = stress_penalty

        # Reward shaper: transforms raw metrics into shaped rewards
        self.shaper = nn.Sequential(
            nn.Linear(5, 16),  # 5 input factors
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Tanh()  # Reward in [-1, 1]
        )

        if device:
            self.to(device)

    def compute_phi_reward(self, phi: torch.Tensor) -> torch.Tensor:
        """
        Reward for high φ-depth.

        Args:
            phi: φ-depth value

        Returns:
            reward: φ reward
        """
        phi_val = phi.mean() if phi.numel() > 1 else phi
        # Reward increases with φ
        reward = torch.tanh(5 * (phi_val - 0.3))
        return reward * self.phi_weight

    def compute_coherence_reward(self, coherence: torch.Tensor) -> torch.Tensor:
        """
        Reward for high coherence.

        Args:
            coherence: Coherence values

        Returns:
            reward: Coherence reward
        """
        coh_mean = coherence.mean()
        reward = torch.tanh(5 * (coh_mean - 0.5))
        return reward * self.coherence_weight

    def compute_alignment_reward(self, align: torch.Tensor) -> torch.Tensor:
        """
        Reward for goal alignment.

        Args:
            align: Alignment values

        Returns:
            reward: Alignment reward
        """
        align_mean = align.mean()
        reward = torch.tanh(5 * align_mean)
        return reward * self.alignment_weight

    def compute_stability_reward(self, stability: torch.Tensor) -> torch.Tensor:
        """
        Reward for stability.

        Args:
            stability: Meta-stability value

        Returns:
            reward: Stability reward
        """
        reward = torch.tanh(5 * (stability - 0.5))
        return reward * self.stability_weight

    def compute_stress_penalty(self, stress: torch.Tensor) -> torch.Tensor:
        """
        Penalty for high stress.

        Args:
            stress: Stress level

        Returns:
            penalty: Stress penalty (negative)
        """
        stress_val = stress.mean() if stress.numel() > 1 else stress
        penalty = -torch.tanh(5 * stress_val)
        return penalty * self.stress_penalty

    def compute_raw_reward(
        self,
        phi: torch.Tensor,
        coherence: torch.Tensor,
        align: torch.Tensor,
        stability: torch.Tensor,
        stress: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute raw reward from components.

        Args:
            phi: φ-depth
            coherence: Coherence values
            align: Alignment values
            stability: Meta-stability
            stress: Stress level

        Returns:
            raw_reward: Sum of weighted components
        """
        phi_r = self.compute_phi_reward(phi)
        coh_r = self.compute_coherence_reward(coherence)
        align_r = self.compute_alignment_reward(align)
        stab_r = self.compute_stability_reward(stability)
        stress_p = self.compute_stress_penalty(stress)

        raw_reward = phi_r + coh_r + align_r + stab_r + stress_p

        return raw_reward

    def shape_reward(
        self,
        phi: torch.Tensor,
        coherence: torch.Tensor,
        align: torch.Tensor,
        stability: torch.Tensor,
        stress: torch.Tensor
    ) -> torch.Tensor:
        """
        Apply neural shaping to raw reward.

        Args:
            phi, coherence, align, stability, stress: Input factors

        Returns:
            shaped_reward: Shaped reward [-1, 1]
        """
        # Extract scalars
        phi_val = phi.mean() if phi.numel() > 1 else phi
        coh_val = coherence.mean()
        align_val = align.mean()
        stab_val = stability.mean() if stability.numel() > 1 else stability
        stress_val = stress.mean() if stress.numel() > 1 else stress

        # Create feature vector
        features = torch.cat([
            phi_val.unsqueeze(0) if phi_val.ndim == 0 else phi_val,
            coh_val.unsqueeze(0) if coh_val.ndim == 0 else coh_val,
            align_val.unsqueeze(0) if align_val.ndim == 0 else align_val,
            stab_val.unsqueeze(0) if stab_val.ndim == 0 else stab_val,
            stress_val.unsqueeze(0) if stress_val.ndim == 0 else stress_val
        ])

        # Shape
        shaped = self.shaper(features)

        return shaped.squeeze()

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Compute harmonic reward.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with raw_reward, shaped_reward, reward_components
        """
        phi = hybrid_out['phi']
        coherence = hybrid_out['coherence']
        align = hybrid_out.get('align', torch.zeros(8))
        stability = state.get('meta_stability', torch.tensor(0.5))
        stress = state.get('stress_level', torch.tensor(0.0))

        # Compute raw reward
        raw_reward = self.compute_raw_reward(phi, coherence, align, stability, stress)

        # Shape reward
        shaped_reward = self.shape_reward(phi, coherence, align, stability, stress)

        return {
            'raw_reward': raw_reward,
            'shaped_reward': shaped_reward,
            'reward_components': {
                'phi_reward': self.compute_phi_reward(phi),
                'coherence_reward': self.compute_coherence_reward(coherence),
                'alignment_reward': self.compute_alignment_reward(align),
                'stability_reward': self.compute_stability_reward(stability),
                'stress_penalty': self.compute_stress_penalty(stress)
            }
        }
