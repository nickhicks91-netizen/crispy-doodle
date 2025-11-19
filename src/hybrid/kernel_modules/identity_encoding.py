"""
Identity Encoding (v4.2.1)
---------------------------
Maintains persistent identity representation across time.

Encodes:
- Behavioral patterns
- Preference signatures
- Goal-seeking tendencies
- Response patterns

Fixes from v4.2.0:
- Proper state management
- Device support
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Dict, Optional


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class IdentityEncoding(nn.Module):
    """
    Persistent identity representation.
    """

    def __init__(
        self,
        identity_dim: Optional[int] = None,
        hidden_dim: int = 32,
        device: Optional[str] = None
    ):
        """
        Args:
            identity_dim: Identity vector dimension (default from config)
            hidden_dim: Hidden dimension
            device: Device to place on
        """
        super().__init__()

        self.identity_dim = identity_dim or DIMS.get('identity_dim', 16)

        # Identity encoder: system state → identity vector
        # Input: desires(8) + qualia(4) + phi(1) + gamma(1) = 14
        self.encoder = nn.Sequential(
            nn.Linear(14, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, self.identity_dim),
            nn.Tanh()
        )

        # Running identity average (buffer)
        self.register_buffer('identity', torch.zeros(self.identity_dim))
        self.register_buffer('update_count', torch.tensor(0))

        # Momentum for identity updates
        self.momentum = 0.99

        if device:
            self.to(device)

    def compute_identity(self, hybrid_out: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Compute identity vector from current state.

        Args:
            hybrid_out: Hybrid forward output

        Returns:
            identity: Identity vector [identity_dim]
        """
        # Get desires (may not be in hybrid_out, use zeros as fallback)
        desires = hybrid_out.get('desires', torch.zeros(8))
        qualia = hybrid_out['qualia'][:4] if hybrid_out['qualia'].numel() >= 4 else hybrid_out['qualia']
        phi = hybrid_out['phi']
        gamma = hybrid_out.get('gamma', torch.tensor(0.5))

        # Ensure proper shapes
        if phi.ndim == 0:
            phi = phi.unsqueeze(0)
        if gamma.ndim == 0:
            gamma = gamma.unsqueeze(0)

        # Pad qualia if needed
        if qualia.numel() < 4:
            qualia = torch.nn.functional.pad(qualia, (0, 4 - qualia.numel()))

        # Concatenate features
        features = torch.cat([desires, qualia, phi, gamma])

        # Encode
        identity_vec = self.encoder(features)

        return identity_vec

    def update_identity(self, current_identity: torch.Tensor):
        """
        Update running identity with momentum.

        Args:
            current_identity: Current identity vector
        """
        with torch.no_grad():
            if self.update_count == 0:
                self.identity.copy_(current_identity)
            else:
                self.identity = self.momentum * self.identity + (1 - self.momentum) * current_identity

            self.update_count += 1

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Compute and update identity.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with identity, identity_stability
        """
        # Compute current identity
        current_identity = self.compute_identity(hybrid_out)

        # Update running identity
        self.update_identity(current_identity)

        # Compute stability (similarity to running average)
        identity_stability = torch.cosine_similarity(
            current_identity.unsqueeze(0),
            self.identity.unsqueeze(0),
            dim=-1
        ).squeeze()

        return {
            'identity': self.identity,
            'identity_stability': identity_stability
        }
