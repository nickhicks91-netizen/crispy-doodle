"""
Context Windows (v4.2.1)
-------------------------
Maintains multiple temporal context windows at different scales.

Windows:
- Short-term: last 10 ticks
- Medium-term: last 100 ticks
- Long-term: last 1000 ticks

Tracks:
- ψ-state evolution patterns
- φ-depth trajectories
- Coherence trends
"""

import torch
import torch.nn as nn
from typing import Dict, Optional, List
from collections import deque


class ContextWindows(nn.Module):
    """
    Multi-scale temporal context tracking.
    """

    def __init__(
        self,
        short_window: int = 10,
        medium_window: int = 100,
        long_window: int = 1000,
        feature_dim: int = 8,
        device: Optional[str] = None
    ):
        """
        Args:
            short_window: Short-term window size
            medium_window: Medium-term window size
            long_window: Long-term window size
            feature_dim: Dimension of features to track
            device: Device to place on
        """
        super().__init__()

        self.short_window = short_window
        self.medium_window = medium_window
        self.long_window = long_window
        self.feature_dim = feature_dim

        # History buffers (using deque for efficient append/pop)
        self.short_history = deque(maxlen=short_window)
        self.medium_history = deque(maxlen=medium_window)
        self.long_history = deque(maxlen=long_window)

        # Aggregators for each window
        self.short_agg = nn.Linear(feature_dim, feature_dim)
        self.medium_agg = nn.Linear(feature_dim, feature_dim)
        self.long_agg = nn.Linear(feature_dim, feature_dim)

        if device:
            self.to(device)

    def extract_features(self, hybrid_out: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Extract trackable features from hybrid output.

        Args:
            hybrid_out: Hybrid forward output

        Returns:
            features: Feature vector [feature_dim]
        """
        phi = hybrid_out['phi']
        coherence = hybrid_out['coherence']
        qualia = hybrid_out['qualia']

        # Aggregate to fixed dimension
        phi_val = phi.mean() if phi.numel() > 1 else phi
        coh_val = coherence.mean()
        qualia_vals = qualia[:4] if qualia.numel() >= 4 else torch.nn.functional.pad(qualia, (0, 4 - qualia.numel()))

        features = torch.cat([
            phi_val.unsqueeze(0) if phi_val.ndim == 0 else phi_val,
            coh_val.unsqueeze(0) if coh_val.ndim == 0 else coh_val,
            qualia_vals[:2]  # Use first 2 qualia channels
        ])

        # Pad or truncate to feature_dim
        if features.numel() < self.feature_dim:
            features = torch.nn.functional.pad(features, (0, self.feature_dim - features.numel()))
        else:
            features = features[:self.feature_dim]

        return features

    def update(self, hybrid_out: Dict[str, torch.Tensor]):
        """
        Update all context windows with new observation.

        Args:
            hybrid_out: Hybrid forward output
        """
        features = self.extract_features(hybrid_out)

        # Add to all windows
        self.short_history.append(features)
        self.medium_history.append(features)
        self.long_history.append(features)

    def aggregate_window(
        self,
        history: deque,
        aggregator: nn.Module
    ) -> torch.Tensor:
        """
        Aggregate history window.

        Args:
            history: Deque of historical features
            aggregator: Aggregation module

        Returns:
            aggregated: Aggregated context [feature_dim]
        """
        if len(history) == 0:
            return torch.zeros(self.feature_dim)

        # Stack history
        stacked = torch.stack(list(history))  # [window_size, feature_dim]

        # Average pool
        pooled = stacked.mean(dim=0)  # [feature_dim]

        # Apply aggregator
        aggregated = aggregator(pooled)

        return aggregated

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Update and return context windows.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with short_context, medium_context, long_context
        """
        # Update windows
        self.update(hybrid_out)

        # Aggregate each window
        short_context = self.aggregate_window(self.short_history, self.short_agg)
        medium_context = self.aggregate_window(self.medium_history, self.medium_agg)
        long_context = self.aggregate_window(self.long_history, self.long_agg)

        return {
            'short_context': short_context,
            'medium_context': medium_context,
            'long_context': long_context
        }
