"""
Predictive Attention (v4.2.1)
------------------------------
Attention mechanism that predicts what to focus on before it's needed.

Predicts:
- Which ψ nodes will be important
- Which memory patterns to prioritize
- Which subsystems to pre-activate

Fixes from v4.2.0:
- Proper state management
- Batching support
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


class PredictiveAttention(nn.Module):
    """
    Predictive attention over ψ-nodes and memory.
    """

    def __init__(
        self,
        N: Optional[int] = None,
        memory_dim: Optional[int] = None,
        device: Optional[str] = None
    ):
        """
        Args:
            N: Number of ψ nodes
            memory_dim: Memory dimension
            device: Device to place on
        """
        super().__init__()

        self.N = N or DIMS['N']
        self.memory_dim = memory_dim or DIMS['memory_dim']

        # ψ-node attention predictor
        self.psi_attention = nn.Sequential(
            nn.Linear(self.N, 64),
            nn.ReLU(),
            nn.Linear(64, self.N),
            nn.Softmax(dim=-1)
        )

        # Memory attention predictor
        self.memory_attention = nn.Sequential(
            nn.Linear(self.memory_dim, 64),
            nn.ReLU(),
            nn.Linear(64, self.memory_dim),
            nn.Sigmoid()
        )

        if device:
            self.to(device)

    def attend_psi(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Compute attention weights over ψ nodes.

        Args:
            psi: Complex ψ state [N] or [batch, N]

        Returns:
            attention: Attention weights [N] or [batch, N]
        """
        # Use real part
        psi_real = torch.real(psi)

        # Compute attention
        attention = self.psi_attention(psi_real)

        return attention

    def attend_memory(self, memory: torch.Tensor) -> torch.Tensor:
        """
        Compute attention weights over memory.

        Args:
            memory: Memory vector [memory_dim] or [batch, memory_dim]

        Returns:
            attention: Attention weights [memory_dim] or [batch, memory_dim]
        """
        attention = self.memory_attention(memory)
        return attention

    def apply_attention(
        self,
        psi: torch.Tensor,
        psi_attention: torch.Tensor,
        memory: torch.Tensor,
        memory_attention: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Apply attention to focus resources.

        Args:
            psi: ψ state
            psi_attention: ψ attention weights
            memory: Memory state
            memory_attention: Memory attention weights

        Returns:
            Dictionary with attended_psi, attended_memory
        """
        # Apply attention (element-wise multiplication)
        psi_real = torch.real(psi)
        attended_psi = psi_real * psi_attention

        attended_memory = memory * memory_attention

        return {
            'attended_psi': attended_psi,
            'attended_memory': attended_memory
        }

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Compute predictive attention.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with psi_attention, memory_attention, attended states
        """
        psi = hybrid_out['psi']
        memory = hybrid_out['memory']

        # Compute attention
        psi_attn = self.attend_psi(psi)
        memory_attn = self.attend_memory(memory)

        # Apply attention
        attended = self.apply_attention(psi, psi_attn, memory, memory_attn)

        return {
            'psi_attention': psi_attn,
            'memory_attention': memory_attn,
            **attended
        }
