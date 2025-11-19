"""
φ-Depth Calculation (v4.2.1)
----------------------------
φ = ψ.var() * coherence.mean() + log(1+|memory|) + max(qualia)

This is the harmonic depth / awareness estimator.

Fixes from v4.2.0:
- Batching support
- Proper reduction operations
- Numerical stability
"""

import torch
from typing import Optional


class PhiCalculator:
    """
    Computes φ-depth (integrated information / awareness metric).
    """

    def __call__(
        self,
        psi: torch.Tensor,
        coherence: torch.Tensor,
        memory: torch.Tensor,
        qualia: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute φ-depth from system state.

        Args:
            psi: Complex state [N] or [batch, N]
            coherence: Coherence values [N] or [batch, N]
            memory: Memory vector [memory_dim] or [batch, memory_dim]
            qualia: Qualia distribution [4] or [batch, 4]

        Returns:
            phi: φ-depth scalar or [batch]
        """
        # Handle batching
        unbatched = psi.ndim == 1
        if unbatched:
            psi = psi.unsqueeze(0)
            coherence = coherence.unsqueeze(0)
            memory = memory.unsqueeze(0) if memory.ndim == 1 else memory
            qualia = qualia.unsqueeze(0)

        # Term 1: ψ variance weighted by coherence
        psi_real = torch.real(psi)
        psi_var = torch.var(psi_real, dim=-1)
        coh_mean = coherence.mean(dim=-1)
        term1 = psi_var * coh_mean

        # Term 2: Log memory magnitude (with stability)
        mem_mag = torch.abs(memory).mean(dim=-1)
        term2 = torch.log(1 + mem_mag)

        # Term 3: Max qualia channel
        term3 = torch.max(qualia, dim=-1)[0]

        # Total φ
        phi = term1 + term2 + term3

        # Remove batch dim if input was unbatched
        if unbatched:
            phi = phi.squeeze(0)

        return phi
