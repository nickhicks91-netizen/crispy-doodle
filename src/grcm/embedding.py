"""
Harmonic Embedding Module (v4.2.1)
-----------------------------------
Implements:
    freq = tanh(linear(grounded → frequency_dim))
    η = freq.norm()
    φ = angle(fft(freq))
    I = η * exp(iφ)

This is the GRCM harmonic drive that feeds into ψ-dynamics.

Fixes from v4.2.0 (Issue #3):
- I is now properly broadcasted to [N] to match ψ dimension
- Batching support
- Device management
- Validation
"""

import torch
import torch.nn as nn
import torch.fft as fft
import yaml
from pathlib import Path
from typing import Optional, Tuple
from ..core.errors import DimensionMismatchError


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class HarmonicEmbedding(nn.Module):
    """
    Converts grounded input to harmonic drive signal for ψ-dynamics.
    """

    def __init__(
        self,
        grounded_dim: Optional[int] = None,
        freq_dim: Optional[int] = None,
        N: Optional[int] = None,
        device: Optional[str] = None
    ):
        """
        Args:
            grounded_dim: Grounding dimension (default from config)
            freq_dim: Frequency dimension (default from config)
            N: Number of ψ nodes (for I broadcast, default from config)
            device: Device to place on
        """
        super().__init__()

        self.grounded_dim = grounded_dim or DIMS['grounding_dim']
        self.freq_dim = freq_dim or DIMS['frequency_dim']
        self.N = N or DIMS['N']

        # Linear projection to frequency space
        self.linear = nn.Linear(self.grounded_dim, self.freq_dim)

        if device:
            self.to(device)

    def forward(self, grounded: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute harmonic embedding and drive signal.

        Args:
            grounded: Grounding vector [grounding_dim] or [batch, grounding_dim]

        Returns:
            freq: Frequency representation [freq_dim] or [batch, freq_dim]
            I: Harmonic drive [N] or [batch, N] (complex)
        """
        # Handle batching
        unbatched = grounded.ndim == 1
        if unbatched:
            grounded = grounded.unsqueeze(0)

        # Validate dimension
        if grounded.shape[-1] != self.grounded_dim:
            raise DimensionMismatchError(
                f"Expected grounded dim {self.grounded_dim}, got {grounded.shape[-1]}"
            )

        batch_size = grounded.shape[0]

        # Project to frequency space
        freq = torch.tanh(self.linear(grounded))  # [batch, freq_dim]

        # Compute magnitude
        eta = torch.norm(freq, dim=-1, keepdim=True)  # [batch, 1]

        # Compute phase via FFT
        fft_out = fft.fft(freq, dim=-1)  # [batch, freq_dim]
        phi = torch.angle(fft_out)  # [batch, freq_dim]

        # Take mean phase for broadcast
        phi_mean = phi.mean(dim=-1, keepdim=True)  # [batch, 1]

        # Compute complex drive: I = η * exp(iφ)
        I_base = eta * torch.exp(1j * phi_mean)  # [batch, 1]

        # Broadcast to match ψ dimension [N]
        I = I_base.repeat(1, self.N)  # [batch, N]

        # Remove batch dim if input was unbatched
        if unbatched:
            freq = freq.squeeze(0)
            I = I.squeeze(0)

        return freq, I
