"""
Stability Metrics for EchoZero (v4.2.1)
----------------------------------------
Provides:
- ψ-energy
- ψ-drift
- Coherence index
- Spectral stability

Fixes: Batching support, proper reduction
"""

import torch


def psi_energy(psi: torch.Tensor) -> torch.Tensor:
    """
    Compute total energy of ψ state.

    Args:
        psi: Complex state [N] or [batch, N]

    Returns:
        energy: Total energy scalar or [batch]
    """
    energy = torch.sum(torch.abs(psi) ** 2, dim=-1)
    return energy.real


def psi_drift(psi_prev: torch.Tensor, psi_curr: torch.Tensor) -> torch.Tensor:
    """
    Compute drift between consecutive states.

    Args:
        psi_prev: Previous state [N] or [batch, N]
        psi_curr: Current state [N] or [batch, N]

    Returns:
        drift: Mean absolute difference
    """
    diff = torch.abs(psi_curr - psi_prev)
    drift = torch.mean(diff, dim=-1)
    return drift.real


def coherence_index(psi: torch.Tensor, node_freqs: torch.Tensor) -> torch.Tensor:
    """
    Compute coherence: sigmoid(10 * (1 - |ψ - node_freqs|))

    Args:
        psi: Complex state [N] or [batch, N]
        node_freqs: Node frequencies [N]

    Returns:
        coherence: [N] or [batch, N]
    """
    psi_real = torch.real(psi)
    deviation = torch.abs(psi_real - node_freqs)
    coherence = torch.sigmoid(10 * (1 - deviation))
    return coherence


def spectral_stability(K: torch.Tensor) -> torch.Tensor:
    """
    Compute spectral radius of coupling matrix.

    Args:
        K: Coupling matrix [N, N]

    Returns:
        max_eigenvalue: Largest eigenvalue magnitude
    """
    eigs = torch.linalg.eigvals(K)
    max_eig = torch.max(torch.abs(eigs))
    return max_eig.real
