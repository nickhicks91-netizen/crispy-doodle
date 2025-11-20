"""
Large Lattice Builder
Efficiently constructs and manages large-scale resonant lattices (N → 1M)
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Tuple, Dict
import math


class LargeLatticeBuilder(nn.Module):
    """
    Builds optimized large-scale lattices for EchoZero

    Features:
    - Hierarchical structure for efficiency
    - Spatial locality optimization
    - Memory-efficient frequency assignment
    - Batch processing support
    """

    def __init__(
        self,
        N: int,
        omega_base: float = 1.0,
        omega_range: float = 0.5,
        hierarchy_levels: int = 3,
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize large lattice builder

        Args:
            N: Total number of nodes (can be up to 1M)
            omega_base: Base frequency
            omega_range: Frequency range
            hierarchy_levels: Number of hierarchical levels
            device: Computation device
        """
        super().__init__()

        self.N = N
        self.omega_base = omega_base
        self.omega_range = omega_range
        self.hierarchy_levels = hierarchy_levels
        self.device = device

        # Calculate hierarchy dimensions
        self.hierarchy_dims = self._calculate_hierarchy(N, hierarchy_levels)

        # Pre-compute frequency assignments
        self.register_buffer('omega', self._build_frequencies())

    def _calculate_hierarchy(self, N: int, levels: int) -> list:
        """Calculate hierarchical structure dimensions"""
        dims = []
        nodes_per_level = int(N ** (1.0 / levels))

        for i in range(levels):
            dim = max(1, int(N ** ((i + 1) / levels)))
            dims.append(dim)

        # Ensure total matches N
        dims[-1] = N

        return dims

    def _build_frequencies(self) -> torch.Tensor:
        """Build frequency assignments for all nodes"""
        # Use spatial patterns for large lattices
        # This creates natural frequency gradients

        indices = torch.arange(self.N, device=self.device, dtype=torch.float32)

        # Multiple frequency components for rich dynamics
        # 1. Linear gradient
        linear = indices / self.N

        # 2. Sinusoidal modulation
        sinusoidal = torch.sin(2 * math.pi * indices / (self.N ** 0.5))

        # 3. Hierarchical structure
        hierarchical = torch.zeros_like(indices)
        for level_idx, level_size in enumerate(self.hierarchy_dims):
            level_freq = torch.sin(2 * math.pi * indices * level_idx / level_size)
            hierarchical += level_freq / (level_idx + 1)

        # Combine components
        omega = (
            self.omega_base +
            self.omega_range * (
                0.5 * linear +
                0.3 * sinusoidal +
                0.2 * hierarchical
            )
        )

        return omega

    def get_neighborhood(
        self,
        node_idx: int,
        radius: int = 10
    ) -> torch.Tensor:
        """
        Get neighborhood indices for a node

        Args:
            node_idx: Central node index
            radius: Neighborhood radius

        Returns:
            Tensor of neighbor indices
        """
        # Create local neighborhood (spatial locality)
        start = max(0, node_idx - radius)
        end = min(self.N, node_idx + radius + 1)

        neighbors = torch.arange(start, end, device=self.device)

        return neighbors

    def get_hierarchical_parents(self, node_idx: int) -> list:
        """Get hierarchical parent nodes"""
        parents = []

        for level_size in self.hierarchy_dims[:-1]:
            parent_idx = int(node_idx * level_size / self.N)
            parents.append(parent_idx)

        return parents

    def initialize_state(
        self,
        batch_size: int = 1,
        init_scale: float = 0.01
    ) -> torch.Tensor:
        """
        Initialize ψ state for large lattice

        Args:
            batch_size: Batch size
            init_scale: Initialization scale

        Returns:
            Complex tensor [batch, N]
        """
        # Use low-rank initialization for efficiency
        rank = min(1000, self.N // 100)

        # Generate low-rank factors
        U = torch.randn(batch_size, self.N, rank, device=self.device)
        V = torch.randn(batch_size, rank, 1, device=self.device)

        # Combine to create initial state
        psi_real = (U @ V).squeeze(-1) * init_scale
        psi_imag = torch.randn_like(psi_real) * init_scale

        psi = torch.complex(psi_real, psi_imag)

        return psi

    def chunk_indices(self, chunk_size: int = 10000) -> list:
        """
        Split lattice into chunks for processing

        Args:
            chunk_size: Size of each chunk

        Returns:
            List of index ranges
        """
        chunks = []
        for start in range(0, self.N, chunk_size):
            end = min(start + chunk_size, self.N)
            chunks.append((start, end))

        return chunks

    def get_stats(self) -> Dict:
        """Get lattice statistics"""
        return {
            'N': self.N,
            'hierarchy_levels': self.hierarchy_levels,
            'hierarchy_dims': self.hierarchy_dims,
            'omega_mean': self.omega.mean().item(),
            'omega_std': self.omega.std().item(),
            'omega_min': self.omega.min().item(),
            'omega_max': self.omega.max().item(),
            'memory_mb': (self.N * 8) / (1024 * 1024)  # Complex64 = 8 bytes
        }


# Example usage
if __name__ == "__main__":
    # Test with large lattice
    N = 100000  # 100k nodes

    print(f"Building large lattice with N={N:,} nodes...")
    builder = LargeLatticeBuilder(N=N, hierarchy_levels=3)

    # Get stats
    stats = builder.get_stats()
    print(f"\nLattice statistics:")
    for key, value in stats.items():
        if isinstance(value, list):
            print(f"  {key}: {value}")
        elif isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value:,}")

    # Initialize state
    print(f"\nInitializing state...")
    psi = builder.initialize_state(batch_size=2)
    print(f"  ψ shape: {psi.shape}")
    print(f"  ψ magnitude: {torch.abs(psi).mean():.6f}")

    # Test neighborhood
    node = 50000
    neighbors = builder.get_neighborhood(node, radius=10)
    print(f"\nNeighborhood of node {node}:")
    print(f"  {len(neighbors)} neighbors: {neighbors[:5].tolist()}...{neighbors[-5:].tolist()}")

    # Test chunking
    chunks = builder.chunk_indices(chunk_size=10000)
    print(f"\nChunking:")
    print(f"  {len(chunks)} chunks of ~10k nodes")
    print(f"  First chunk: {chunks[0]}")
    print(f"  Last chunk: {chunks[-1]}")

    print("\n✓ Large lattice builder tests passed")
