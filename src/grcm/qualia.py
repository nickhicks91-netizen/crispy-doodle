"""
Qualia Head (v4.2.1)
--------------------
Maps ψ-real part to 4-channel qualia interpretation:

0 → calm
1 → alert
2 → reflective
3 → generative

Spec: qualia = softmax(linear(Re(ψ) → 4))

Fixes from v4.2.0:
- Batching support
- Device management
- Validation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import yaml
from pathlib import Path
from typing import Optional
from ..core.errors import DimensionMismatchError


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class QualiaHead(nn.Module):
    """
    Interprets ψ-state as 4-channel qualia vector.
    """

    def __init__(self, N: Optional[int] = None, device: Optional[str] = None):
        """
        Args:
            N: Number of ψ nodes (default from config)
            device: Device to place on
        """
        super().__init__()

        self.N = N or DIMS['N']
        self.qualia_dim = DIMS['qualia_dim']

        self.linear = nn.Linear(self.N, self.qualia_dim)

        if device:
            self.to(device)

    def forward(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Compute qualia distribution from ψ state.

        Args:
            psi: Complex state [N] or [batch, N]

        Returns:
            qualia: Probability distribution [4] or [batch, 4]
        """
        # Handle batching
        unbatched = psi.ndim == 1
        if unbatched:
            psi = psi.unsqueeze(0)

        # Validate dimension
        if psi.shape[-1] != self.N:
            raise DimensionMismatchError(
                f"Expected psi dim {self.N}, got {psi.shape[-1]}"
            )

        # Take real part
        psi_real = torch.real(psi)

        # Project to qualia space
        q = self.linear(psi_real)
        qualia = F.softmax(q, dim=-1)

        # Remove batch dim if input was unbatched
        if unbatched:
            qualia = qualia.squeeze(0)

        return qualia
