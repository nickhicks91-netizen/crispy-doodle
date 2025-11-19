"""
Desire System (v4.2.1)
----------------------
The GRCM desire vector is a soft goal-conditioning signal.

It is NOT reinforcement learning and NOT backprop-driven.

Desires guide:
- γ modulation in ψ-dynamics
- Forward-pass goal alignment

Fixes from v4.2.0:
- Proper state management (uses buffer not Parameter)
- Device support
- Batching support
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Optional
from ..core.device import to_device


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class DesireModule(nn.Module):
    """
    Learnable desire vector that guides system behavior.

    Note: While desires can be updated, they are NOT trained via backprop.
    Updates happen through external goal-setting or meta-control.
    """

    def __init__(self, dim: Optional[int] = None, device: Optional[str] = None):
        """
        Args:
            dim: Desire dimension (default from config)
            device: Device to place on
        """
        super().__init__()

        self.dim = dim or DIMS['desire_dim']

        # Use buffer (not Parameter) since we don't want autograd tracking
        desires = torch.zeros(self.dim)
        self.register_buffer('desires', desires)

        if device:
            self.to(device)

    def forward(self) -> torch.Tensor:
        """
        Get current desire vector.

        Returns:
            desires: [desire_dim]
        """
        return torch.tanh(self.desires)

    def set_desires(self, new_desires: torch.Tensor):
        """
        Manually update desire vector.

        Args:
            new_desires: New desire values [desire_dim]
        """
        if new_desires.shape[0] != self.dim:
            raise ValueError(f"Expected {self.dim} desires, got {new_desires.shape[0]}")

        self.desires.copy_(new_desires)


def cosine_align(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """
    Compute cosine alignment between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        alignment: Cosine similarity
    """
    a_norm = a / (a.norm() + 1e-8)
    b_norm = b / (b.norm() + 1e-8)
    return torch.dot(a_norm, b_norm)
