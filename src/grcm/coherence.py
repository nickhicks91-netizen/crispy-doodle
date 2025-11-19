"""
Coherence Function (v4.2.1)
----------------------------
coherence = sigmoid(10 * (1 - |ψ - node_freqs|))

Measures how well ψ aligns with node frequencies.

Fixes from v4.2.0:
- Batching support
- Proper broadcasting
"""

import torch


def compute_coherence(psi: torch.Tensor, node_freqs: torch.Tensor) -> torch.Tensor:
    """
    Compute coherence between ψ state and node frequencies.

    Args:
        psi: Complex state [N] or [batch, N]
        node_freqs: Node frequencies [N]

    Returns:
        coherence: Coherence values [N] or [batch, N]
    """
    # Take real part of ψ
    psi_real = torch.real(psi)

    # Compute deviation from ideal frequencies
    # Handle batching: node_freqs broadcasts automatically
    deviation = torch.abs(psi_real - node_freqs)

    # Coherence function
    coherence = torch.sigmoid(10 * (1 - deviation))

    return coherence
