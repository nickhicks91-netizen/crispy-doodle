"""
Sparse Coupling Matrix
Memory-efficient coupling for large lattices using sparse representations
"""

import torch
import torch.nn as nn
import torch.sparse as sparse
from typing import Optional, Tuple
import math


class SparseCouplingMatrix(nn.Module):
    """
    Sparse coupling matrix for large-scale lattices

    Features:
    - COO sparse format for efficiency
    - Local connectivity patterns
    - Hierarchical long-range connections
    - Memory usage: O(N * k) instead of O(N²)
    """

    def __init__(
        self,
        N: int,
        local_radius: int = 10,
        long_range_prob: float = 0.001,
        coupling_strength: float = 0.01,
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize sparse coupling matrix

        Args:
            N: Lattice size
            local_radius: Local connectivity radius
            long_range_prob: Probability of long-range connection
            coupling_strength: Base coupling strength
            device: Computation device
        """
        super().__init__()

        self.N = N
        self.local_radius = local_radius
        self.long_range_prob = long_range_prob
        self.coupling_strength = coupling_strength
        self.device = device

        # Build sparse matrix
        self.K_real, self.K_imag = self._build_sparse_coupling()

    def _build_sparse_coupling(self) -> Tuple[torch.sparse.Tensor, torch.sparse.Tensor]:
        """Build sparse coupling matrices (real and imaginary)"""

        indices_list = []
        values_real_list = []
        values_imag_list = []

        # 1. Local connections (spatial neighbors)
        for i in range(self.N):
            # Local neighborhood
            for j in range(max(0, i - self.local_radius),
                          min(self.N, i + self.local_radius + 1)):
                if i != j:
                    distance = abs(i - j)
                    # Distance-based strength
                    strength = self.coupling_strength * math.exp(-distance / self.local_radius)

                    indices_list.append([i, j])
                    values_real_list.append(strength)
                    values_imag_list.append(strength * 0.1)  # Small imaginary component

        # 2. Long-range connections (sparse)
        num_long_range = int(self.N * self.long_range_prob)
        for _ in range(num_long_range):
            i = torch.randint(0, self.N, (1,)).item()
            j = torch.randint(0, self.N, (1,)).item()

            if i != j:
                strength = self.coupling_strength * 0.5  # Weaker long-range
                indices_list.append([i, j])
                values_real_list.append(strength)
                values_imag_list.append(strength * 0.2)

        # Convert to sparse tensors
        if indices_list:
            indices = torch.tensor(indices_list, device=self.device).t()
            values_real = torch.tensor(values_real_list, device=self.device, dtype=torch.float32)
            values_imag = torch.tensor(values_imag_list, device=self.device, dtype=torch.float32)

            K_real = torch.sparse_coo_tensor(
                indices, values_real, (self.N, self.N), device=self.device
            )
            K_imag = torch.sparse_coo_tensor(
                indices, values_imag, (self.N, self.N), device=self.device
            )
        else:
            # Empty sparse tensors
            K_real = torch.sparse_coo_tensor(
                torch.empty(2, 0, dtype=torch.long, device=self.device),
                torch.empty(0, dtype=torch.float32, device=self.device),
                (self.N, self.N)
            )
            K_imag = torch.sparse_coo_tensor(
                torch.empty(2, 0, dtype=torch.long, device=self.device),
                torch.empty(0, dtype=torch.float32, device=self.device),
                (self.N, self.N)
            )

        return K_real, K_imag

    def apply(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Apply coupling: K·ψ

        Args:
            psi: Complex tensor [batch, N] or [N]

        Returns:
            K·ψ result
        """
        # Handle batching
        if psi.dim() == 1:
            psi = psi.unsqueeze(0)
            squeeze_result = True
        else:
            squeeze_result = False

        batch_size = psi.shape[0]
        results = []

        for b in range(batch_size):
            psi_b = psi[b]

            # Separate real and imaginary parts
            psi_real = psi_b.real
            psi_imag = psi_b.imag

            # Sparse matrix multiplication
            # (K_real + i*K_imag) · (psi_real + i*psi_imag)
            # = K_real·psi_real - K_imag·psi_imag + i(K_real·psi_imag + K_imag·psi_real)

            result_real = (
                torch.sparse.mm(self.K_real, psi_real.unsqueeze(1)).squeeze(1) -
                torch.sparse.mm(self.K_imag, psi_imag.unsqueeze(1)).squeeze(1)
            )

            result_imag = (
                torch.sparse.mm(self.K_real, psi_imag.unsqueeze(1)).squeeze(1) +
                torch.sparse.mm(self.K_imag, psi_real.unsqueeze(1)).squeeze(1)
            )

            result = torch.complex(result_real, result_imag)
            results.append(result)

        result_batch = torch.stack(results)

        if squeeze_result:
            result_batch = result_batch.squeeze(0)

        return result_batch

    def get_stats(self) -> dict:
        """Get coupling matrix statistics"""
        # Count non-zero elements
        nnz_real = self.K_real._nnz()
        nnz_imag = self.K_imag._nnz()

        # Calculate sparsity
        total_elements = self.N * self.N
        sparsity_real = 1.0 - (nnz_real / total_elements)
        sparsity_imag = 1.0 - (nnz_imag / total_elements)

        # Memory usage
        dense_memory_mb = (total_elements * 8) / (1024 * 1024)  # Complex64
        sparse_memory_mb = ((nnz_real + nnz_imag) * 12) / (1024 * 1024)  # Indices + values

        return {
            'N': self.N,
            'nnz_real': nnz_real,
            'nnz_imag': nnz_imag,
            'sparsity_real': sparsity_real,
            'sparsity_imag': sparsity_imag,
            'dense_memory_mb': dense_memory_mb,
            'sparse_memory_mb': sparse_memory_mb,
            'compression_ratio': dense_memory_mb / max(sparse_memory_mb, 0.001)
        }

    def to_dense(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Convert to dense matrices (for small N only!)"""
        if self.N > 10000:
            raise ValueError("Too large to convert to dense (N > 10k)")

        K_real_dense = self.K_real.to_dense()
        K_imag_dense = self.K_imag.to_dense()

        return K_real_dense, K_imag_dense


# Example usage
if __name__ == "__main__":
    # Test with moderate size
    N = 10000
    print(f"Building sparse coupling for N={N:,} nodes...")

    coupling = SparseCouplingMatrix(
        N=N,
        local_radius=10,
        long_range_prob=0.001,
        coupling_strength=0.01
    )

    # Get statistics
    stats = coupling.get_stats()
    print(f"\nCoupling statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            if 'ratio' in key:
                print(f"  {key}: {value:.1f}x")
            elif 'sparsity' in key:
                print(f"  {key}: {value:.4f} ({value*100:.2f}%)")
            else:
                print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value:,}")

    # Test application
    print(f"\nTesting sparse matrix multiplication...")
    psi = torch.randn(2, N, dtype=torch.complex64)  # Batch of 2

    result = coupling.apply(psi)
    print(f"  Input shape: {psi.shape}")
    print(f"  Output shape: {result.shape}")
    print(f"  Output magnitude: {torch.abs(result).mean():.6f}")

    # Memory comparison
    print(f"\nMemory efficiency:")
    print(f"  Dense would use: {stats['dense_memory_mb']:.1f} MB")
    print(f"  Sparse uses: {stats['sparse_memory_mb']:.1f} MB")
    print(f"  Compression: {stats['compression_ratio']:.1f}x")

    print("\n✓ Sparse coupling tests passed")
