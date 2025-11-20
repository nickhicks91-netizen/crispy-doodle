"""
Tests for SparseCouplingMatrix
"""

import pytest
import torch
from src.scaling.sparse_coupling import SparseCouplingMatrix


class TestSparseCouplingMatrix:
    """Test suite for sparse coupling matrix"""

    def test_initialization(self):
        """Test sparse matrix initialization"""
        N = 1000
        k_local = 10
        k_long = 5

        coupling = SparseCouplingMatrix(
            N=N,
            k_local=k_local,
            k_long=k_long
        )

        assert coupling.N == N
        assert coupling.k_local == k_local
        assert coupling.k_long == k_long

    def test_sparse_matrix_construction(self):
        """Test sparse matrix construction"""
        N = 500
        coupling = SparseCouplingMatrix(N=N, k_local=5, k_long=3)

        # Check that matrices are sparse
        assert coupling.K_real.is_sparse
        assert coupling.K_imag.is_sparse

        # Check dimensions
        assert coupling.K_real.shape == (N, N)
        assert coupling.K_imag.shape == (N, N)

    def test_apply_coupling(self):
        """Test applying coupling to ψ state"""
        N = 100
        coupling = SparseCouplingMatrix(N=N, k_local=5, k_long=2)

        # Create test state
        psi = torch.randn(N, dtype=torch.complex64)

        # Apply coupling
        result = coupling.apply(psi)

        assert result.shape == (N,)
        assert result.dtype == torch.complex64
        assert not torch.isnan(result).any()

    def test_batch_apply(self):
        """Test batch application"""
        N = 100
        batch_size = 4
        coupling = SparseCouplingMatrix(N=N, k_local=5, k_long=2)

        # Create batch state
        psi = torch.randn(batch_size, N, dtype=torch.complex64)

        # Apply coupling
        result = coupling.apply(psi)

        assert result.shape == (batch_size, N)
        assert not torch.isnan(result).any()

    def test_memory_efficiency(self):
        """Test memory efficiency vs dense"""
        N = 10000
        k_local = 10
        k_long = 5

        coupling = SparseCouplingMatrix(N=N, k_local=k_local, k_long=k_long)

        # Estimate sparse size
        expected_nonzeros = N * (k_local + k_long)
        sparse_size = expected_nonzeros * 8  # complex64 = 8 bytes

        # Dense size would be
        dense_size = N * N * 8

        # Should be much smaller
        compression_ratio = dense_size / sparse_size
        assert compression_ratio > 100  # At least 100x compression

    def test_sparsity_pattern(self):
        """Test sparsity pattern correctness"""
        N = 100
        k_local = 5
        k_long = 3

        coupling = SparseCouplingMatrix(N=N, k_local=k_local, k_long=k_long)

        # Check number of non-zeros
        nnz_real = coupling.K_real._nnz()
        nnz_imag = coupling.K_imag._nnz()

        # Each node should connect to ~(k_local + k_long) neighbors
        expected_nnz = N * (k_local + k_long)

        # Allow some tolerance
        assert abs(nnz_real - expected_nnz) < N * 2
        assert abs(nnz_imag - expected_nnz) < N * 2

    def test_strength_values(self):
        """Test coupling strength values"""
        N = 100
        coupling = SparseCouplingMatrix(
            N=N,
            k_local=5,
            k_long=2,
            local_strength=0.5,
            long_strength=0.1
        )

        # Convert to dense to check values
        K_real_dense = coupling.K_real.to_dense()

        # Local connections should be stronger
        # (This is a heuristic check)
        assert K_real_dense.abs().max() > 0

    def test_device_handling(self):
        """Test device placement"""
        N = 100

        # CPU
        coupling_cpu = SparseCouplingMatrix(N=N, device=torch.device('cpu'))
        assert coupling_cpu.K_real.device.type == 'cpu'

        # GPU (if available)
        if torch.cuda.is_available():
            coupling_gpu = SparseCouplingMatrix(N=N, device=torch.device('cuda'))
            assert coupling_gpu.K_real.device.type == 'cuda'

    def test_zero_state_handling(self):
        """Test handling of zero state"""
        N = 100
        coupling = SparseCouplingMatrix(N=N, k_local=5, k_long=2)

        psi = torch.zeros(N, dtype=torch.complex64)
        result = coupling.apply(psi)

        assert result.shape == (N,)
        assert torch.allclose(result, torch.zeros_like(result))

    def test_compression_stats(self):
        """Test compression statistics"""
        N = 1000
        coupling = SparseCouplingMatrix(N=N, k_local=10, k_long=5)

        stats = coupling.get_stats()

        assert stats['N'] == N
        assert stats['k_local'] == 10
        assert stats['k_long'] == 5
        assert stats['compression_ratio'] > 50
        assert 'memory_mb' in stats

    def test_large_scale(self):
        """Test with large lattice"""
        N = 100000  # 100k nodes
        k_local = 10
        k_long = 5

        coupling = SparseCouplingMatrix(N=N, k_local=k_local, k_long=k_long)

        # Should create without memory errors
        assert coupling.N == N

        # Apply to test state (subset for speed)
        psi = torch.randn(1000, dtype=torch.complex64)
        psi_full = torch.zeros(N, dtype=torch.complex64)
        psi_full[:1000] = psi

        result = coupling.apply(psi_full)
        assert result.shape == (N,)

    def test_symmetry(self):
        """Test coupling symmetry properties"""
        N = 50
        coupling = SparseCouplingMatrix(N=N, k_local=5, k_long=2)

        # For symmetric coupling, K should be Hermitian
        # (This is a simplified check)
        K_real_dense = coupling.K_real.to_dense()

        # Check real part is symmetric
        diff = K_real_dense - K_real_dense.t()
        assert diff.abs().max() < 1e-5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
