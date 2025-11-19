"""
Alignment & Want Modulation (v4.2.1)
-------------------------------------
γ = 0.2 + 0.4 * sigmoid(align.mean())
align = cos(freq · desires)

Measures alignment between frequency representation and desires.

Fixes from v4.2.0:
- Batching support
- Proper reduction
"""

import torch


def compute_gamma(freq: torch.Tensor, desires: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Compute gamma modulation and alignment.

    Args:
        freq: Frequency vector [freq_dim] or [batch, freq_dim]
        desires: Desire vector [desire_dim]

    Returns:
        gamma: Modulation factor [1] or [batch]
        align: Alignment values [freq_dim] or [batch, freq_dim]
    """
    # Handle batching
    unbatched = freq.ndim == 1
    if unbatched:
        freq = freq.unsqueeze(0)

    batch_size = freq.shape[0]

    # Normalize
    freq_norm = freq / (freq.norm(dim=-1, keepdim=True) + 1e-8)
    desire_norm = desires / (desires.norm() + 1e-8)

    # Compute alignment (broadcasting desires across batch)
    # If freq_dim == desire_dim, use dot product
    if freq.shape[-1] == desires.shape[-1]:
        align = freq_norm * desire_norm
    else:
        # Different dimensions: project to common space
        min_dim = min(freq.shape[-1], desires.shape[-1])
        align = freq_norm[..., :min_dim] * desire_norm[:min_dim]

    # Gamma: 0.2 + 0.4 * sigmoid(mean alignment)
    align_mean = align.mean(dim=-1)  # [batch]
    gamma = 0.2 + 0.4 * torch.sigmoid(align_mean)

    # Remove batch dim if input was unbatched
    if unbatched:
        gamma = gamma.squeeze(0)
        align = align.squeeze(0)

    return gamma, align
