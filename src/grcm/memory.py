"""
Memory Module (GRU) (v4.2.1)
----------------------------
Implements: memory' = GRU(memory, Re(ψ) * coherence)

Memory size: 128-dim (configurable)

This is structured, ordered, and non-transformer.

Fixes from v4.2.0 (Issue #10):
- Does NOT mutate self.memory during forward()
- Returns new memory state (functional style)
- External state management via GlobalState
- Clamping to prevent runaway growth
- Versioning support
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Optional, Tuple
from ..core.errors import DimensionMismatchError


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class MemoryModule(nn.Module):
    """
    GRU-based memory with clamping and functional state updates.

    IMPORTANT: This module does NOT hold persistent state.
    Memory state is managed externally (e.g., in GlobalState).
    """

    def __init__(
        self,
        mem_dim: Optional[int] = None,
        input_dim: int = 1,
        device: Optional[str] = None,
        clamp_range: Tuple[float, float] = (-10.0, 10.0)
    ):
        """
        Args:
            mem_dim: Memory dimension (default from config)
            input_dim: Input feature dimension
            device: Device to place on
            clamp_range: Range to clamp memory values
        """
        super().__init__()

        self.mem_dim = mem_dim or DIMS['memory_dim']
        self.input_dim = input_dim
        self.clamp_min, self.clamp_max = clamp_range

        # GRU cell
        self.gru = nn.GRU(input_dim, self.mem_dim, batch_first=True)

        if device:
            self.to(device)

    def forward(
        self,
        psi: torch.Tensor,
        coherence: torch.Tensor,
        prev_memory: torch.Tensor
    ) -> torch.Tensor:
        """
        Update memory based on ψ state and coherence.

        Args:
            psi: Complex state [N] or [batch, N]
            coherence: Coherence values [N] or [batch, N]
            prev_memory: Previous memory state [mem_dim] or [batch, mem_dim]

        Returns:
            new_memory: Updated memory [mem_dim] or [batch, mem_dim]
        """
        # Handle batching
        unbatched = psi.ndim == 1
        if unbatched:
            psi = psi.unsqueeze(0)
            coherence = coherence.unsqueeze(0)
            prev_memory = prev_memory.unsqueeze(0)

        batch_size = psi.shape[0]
        N = psi.shape[1]

        # Validate memory dimension
        if prev_memory.shape[-1] != self.mem_dim:
            raise DimensionMismatchError(
                f"Expected memory dim {self.mem_dim}, got {prev_memory.shape[-1]}"
            )

        # Create stimulus: Re(ψ) * coherence
        psi_real = torch.real(psi)
        stim = psi_real * coherence  # [batch, N]

        # Reshape for GRU: [batch, seq_len, input_dim]
        stim = stim.unsqueeze(-1)  # [batch, N, 1]

        # Prepare hidden state: [num_layers, batch, mem_dim]
        h0 = prev_memory.unsqueeze(0)  # [1, batch, mem_dim]

        # Run GRU
        _, new_memory = self.gru(stim, h0)

        # Remove layer dimension: [batch, mem_dim]
        new_memory = new_memory.squeeze(0)

        # Clamp to prevent runaway growth
        new_memory = torch.clamp(new_memory, self.clamp_min, self.clamp_max)

        # Remove batch dim if input was unbatched
        if unbatched:
            new_memory = new_memory.squeeze(0)

        return new_memory

    def init_memory(self, batch_size: int = 1, device: Optional[str] = None) -> torch.Tensor:
        """
        Initialize blank memory state.

        Args:
            batch_size: Batch size
            device: Device to place on

        Returns:
            memory: Zero-initialized memory [batch, mem_dim] or [mem_dim]
        """
        if batch_size == 1:
            memory = torch.zeros(self.mem_dim)
        else:
            memory = torch.zeros(batch_size, self.mem_dim)

        if device:
            memory = memory.to(device)
        else:
            memory = memory.to(next(self.parameters()).device)

        return memory
