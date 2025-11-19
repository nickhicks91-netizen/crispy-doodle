"""
Coupling Matrix Utilities (v4.2.1)
-----------------------------------
Provides:
- Generation of stable K matrices
- Spectral radius tuning
- Harmonic ring coupling

Fixes: Proper complex tensor handling, device support
"""

import torch
from ..core.device import to_device


def make_ring_coupling(N: int, strength: float = 0.05, device: str = None) -> torch.Tensor:
    """
    Create ring-topology coupling matrix.

    Args:
        N: Number of nodes
        strength: Coupling strength
        device: Device to place tensor on

    Returns:
        K: Complex coupling matrix [N, N]
    """
    K = torch.zeros(N, N, dtype=torch.cfloat)

    for i in range(N):
        K[i, (i + 1) % N] = strength + 0.0j
        K[i, (i - 1) % N] = strength + 0.0j

    if device:
        K = K.to(device)
    else:
        K = to_device(K)

    return K


def limit_spectral_radius(K: torch.Tensor, radius: float = 0.9) -> torch.Tensor:
    """
    Scales K to ensure stability of ODE evolution.

    Args:
        K: Coupling matrix [N, N]
        radius: Target spectral radius

    Returns:
        K_scaled: Stabilized coupling matrix
    """
    eigvals = torch.linalg.eigvals(K)
    max_mag = torch.max(torch.abs(eigvals))

    if max_mag > radius:
        K = K * (radius / max_mag)

    return K


def make_random_coupling(N: int, sparsity: float = 0.8, strength: float = 0.02) -> torch.Tensor:
    """
    Create random sparse coupling matrix.

    Args:
        N: Number of nodes
        sparsity: Fraction of zero entries
        strength: Base coupling strength

    Returns:
        K: Sparse complex coupling matrix
    """
    # Random real and imaginary components
    K_real = torch.randn(N, N) * strength
    K_imag = torch.randn(N, N) * strength

    # Apply sparsity mask
    mask = torch.rand(N, N) > sparsity
    K_real = K_real * mask
    K_imag = K_imag * mask

    K = torch.complex(K_real, K_imag)

    # Ensure stability
    K = limit_spectral_radius(K, radius=0.9)

    return to_device(K)
