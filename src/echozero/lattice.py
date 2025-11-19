"""
Lattice Builder (v4.2.1)
-------------------------
Builds N-node harmonic lattices with:
- Ring topology
- Torsion groups (N/8 clusters)
- Frequency assignment

Fixes: Device support, configurable dimensions
"""

import torch
import yaml
from pathlib import Path
from typing import Tuple, List
from ..core.device import to_device


# Load dimensions
def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


def build_lattice(N: int = None) -> Tuple[torch.Tensor, List[List[int]]]:
    """
    Creates:
    - Node frequencies (real scalars)
    - Torsion cluster assignment

    Args:
        N: Number of nodes (default from config)

    Returns:
        freqs: Node frequencies [N]
        torsion_groups: List of 8 cluster assignments
    """
    N = N or DIMS['N']

    # Evenly spaced node frequencies
    freqs = torch.linspace(0.5, 2.5, N)
    freqs = to_device(freqs)

    # 8-way torsion partition
    torsion_size = N // 8
    torsion_groups = []

    for i in range(8):
        start = i * torsion_size
        end = (i + 1) * torsion_size if i < 7 else N
        torsion_groups.append(list(range(start, end)))

    return freqs, torsion_groups


def assign_initial_state(N: int = None, scale: float = 0.01) -> torch.Tensor:
    """
    Small complex Gaussian initialization of ψ.

    Args:
        N: Number of nodes
        scale: Initialization scale

    Returns:
        psi0: Initial state [N]
    """
    N = N or DIMS['N']

    real = torch.randn(N) * scale
    imag = torch.randn(N) * scale

    psi0 = torch.complex(real, imag)
    return to_device(psi0)
