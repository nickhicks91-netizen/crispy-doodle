"""
Tests for LargeLatticeBuilder
"""

import pytest
import torch
from src.scaling.large_lattice import LargeLatticeBuilder


class TestLargeLatticeBuilder:
    """Test suite for large lattice construction"""

    def test_initialization(self):
        """Test lattice initialization"""
        N = 10000
        builder = LargeLatticeBuilder(N=N, hierarchy_levels=3)

        assert builder.N == N
        assert builder.omega.shape == (N,)
        assert len(builder.hierarchy_dims) == 3

    def test_hierarchy_calculation(self):
        """Test hierarchical structure calculation"""
        N = 1000
        builder = LargeLatticeBuilder(N=N, hierarchy_levels=3)

        # Last dimension should equal N
        assert builder.hierarchy_dims[-1] == N

        # Dimensions should be increasing
        for i in range(len(builder.hierarchy_dims) - 1):
            assert builder.hierarchy_dims[i] <= builder.hierarchy_dims[i + 1]

    def test_frequency_assignment(self):
        """Test frequency assignments"""
        N = 5000
        builder = LargeLatticeBuilder(N=N, omega_base=1.0, omega_range=0.5)

        # Check frequency range
        assert builder.omega.min() >= 0.5  # base - range/2
        assert builder.omega.max() <= 1.5  # base + range/2

        # Check all frequencies assigned
        assert not torch.isnan(builder.omega).any()
        assert not torch.isinf(builder.omega).any()

    def test_state_initialization(self):
        """Test ψ state initialization"""
        N = 1000
        batch_size = 4
        builder = LargeLatticeBuilder(N=N)

        psi = builder.initialize_state(batch_size=batch_size)

        assert psi.shape == (batch_size, N)
        assert psi.dtype == torch.complex64
        assert not torch.isnan(psi).any()

    def test_neighborhood_retrieval(self):
        """Test neighborhood retrieval"""
        N = 1000
        builder = LargeLatticeBuilder(N=N)

        # Middle node
        neighbors = builder.get_neighborhood(500, radius=10)
        assert len(neighbors) == 21  # 10 left + 1 center + 10 right

        # Edge node (start)
        neighbors = builder.get_neighborhood(5, radius=10)
        assert len(neighbors) == 16  # 0-5 + 6-15

        # Edge node (end)
        neighbors = builder.get_neighborhood(995, radius=10)
        assert len(neighbors) == 16  # 985-995 + 996-999

    def test_chunking(self):
        """Test lattice chunking"""
        N = 10000
        chunk_size = 1000
        builder = LargeLatticeBuilder(N=N)

        chunks = builder.chunk_indices(chunk_size=chunk_size)

        # Check number of chunks
        assert len(chunks) == 10

        # Check chunk sizes
        for start, end in chunks[:-1]:
            assert end - start == chunk_size

        # Check last chunk
        assert chunks[-1][1] == N

    def test_hierarchical_parents(self):
        """Test hierarchical parent retrieval"""
        N = 1000
        builder = LargeLatticeBuilder(N=N, hierarchy_levels=3)

        parents = builder.get_hierarchical_parents(500)

        # Should have hierarchy_levels - 1 parents
        assert len(parents) == 2

        # Parents should be valid indices
        for parent in parents:
            assert 0 <= parent < N

    def test_large_scale(self):
        """Test with very large lattice"""
        N = 100000  # 100k nodes
        builder = LargeLatticeBuilder(N=N, hierarchy_levels=3)

        # Should handle large lattice without errors
        assert builder.omega.shape == (N,)

        # Memory check (should fit in reasonable space)
        stats = builder.get_stats()
        assert stats['memory_mb'] > 0
        assert stats['memory_mb'] < 1000  # Less than 1GB for 100k nodes

    def test_stats_retrieval(self):
        """Test statistics retrieval"""
        N = 1000
        builder = LargeLatticeBuilder(N=N)

        stats = builder.get_stats()

        assert stats['N'] == N
        assert 'omega_mean' in stats
        assert 'omega_std' in stats
        assert 'memory_mb' in stats

    def test_device_handling(self):
        """Test device handling"""
        N = 1000

        # CPU device
        builder_cpu = LargeLatticeBuilder(N=N, device=torch.device('cpu'))
        assert builder_cpu.omega.device.type == 'cpu'

        # GPU device (if available)
        if torch.cuda.is_available():
            builder_gpu = LargeLatticeBuilder(N=N, device=torch.device('cuda'))
            assert builder_gpu.omega.device.type == 'cuda'

    def test_batch_initialization(self):
        """Test batch state initialization"""
        N = 1000
        builder = LargeLatticeBuilder(N=N)

        for batch_size in [1, 2, 8, 16]:
            psi = builder.initialize_state(batch_size=batch_size)
            assert psi.shape[0] == batch_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
