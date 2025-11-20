"""
Tests for DeltaCompressor
"""

import pytest
import torch
from src.scaling.delta_compression import DeltaCompressor


class TestDeltaCompressor:
    """Test suite for delta compression"""

    def test_initialization(self):
        """Test compressor initialization"""
        compressor = DeltaCompressor(
            quantization_bits=16,
            sparse_threshold=1e-6,
            compression_level=6
        )

        assert compressor.quantization_bits == 16
        assert compressor.sparse_threshold == 1e-6
        assert compressor.compression_level == 6

    def test_full_compression(self):
        """Test full state compression (no delta)"""
        N = 1000
        compressor = DeltaCompressor()

        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        # Compress
        compressed = compressor.compress(psi)

        assert isinstance(compressed, bytes)
        assert len(compressed) > 0
        assert len(compressed) < N * 8  # Should be smaller than uncompressed

    def test_delta_compression(self):
        """Test delta compression"""
        N = 1000
        compressor = DeltaCompressor()

        # Create states with small delta
        psi_0 = torch.randn(N, dtype=torch.complex64) * 0.1
        psi_1 = psi_0 + torch.randn(N, dtype=torch.complex64) * 0.01

        # Compress with delta
        compressed_delta = compressor.compress(psi_1, psi_0)

        # Compress without delta
        compressed_full = compressor.compress(psi_1)

        # Delta should be smaller
        assert len(compressed_delta) < len(compressed_full)

    def test_decompression(self):
        """Test decompression accuracy"""
        N = 1000
        compressor = DeltaCompressor(quantization_bits=16)

        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        # Compress and decompress
        compressed = compressor.compress(psi)
        psi_recovered = compressor.decompress(compressed)

        # Check shape
        assert psi_recovered.shape == psi.shape

        # Check error (should be small with 16-bit quantization)
        error = torch.abs(psi - psi_recovered).mean().item()
        assert error < 1e-4

    def test_delta_decompression(self):
        """Test delta decompression"""
        N = 1000
        compressor = DeltaCompressor()

        psi_0 = torch.randn(N, dtype=torch.complex64) * 0.1
        psi_1 = psi_0 + torch.randn(N, dtype=torch.complex64) * 0.01

        # Compress delta
        compressed = compressor.compress(psi_1, psi_0)

        # Decompress with previous state
        psi_1_recovered = compressor.decompress(compressed, psi_0)

        # Check accuracy
        error = torch.abs(psi_1 - psi_1_recovered).mean().item()
        assert error < 1e-4

    def test_batch_compression(self):
        """Test batch compression"""
        N = 1000
        batch_size = 4
        compressor = DeltaCompressor()

        psi_batch = torch.randn(batch_size, N, dtype=torch.complex64) * 0.1

        # Compress
        compressed = compressor.compress(psi_batch)

        # Decompress
        psi_recovered = compressor.decompress(compressed)

        assert psi_recovered.shape == (batch_size, N)

    def test_quantization_levels(self):
        """Test different quantization levels"""
        N = 1000
        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        errors = {}

        for bits in [8, 16, 32]:
            compressor = DeltaCompressor(quantization_bits=bits)

            compressed = compressor.compress(psi)
            psi_recovered = compressor.decompress(compressed)

            error = torch.abs(psi - psi_recovered).mean().item()
            errors[bits] = error

        # Higher bits should give lower error
        assert errors[32] < errors[16] < errors[8]

    def test_sparse_threshold(self):
        """Test sparse threshold effect"""
        N = 1000
        psi_0 = torch.randn(N, dtype=torch.complex64) * 0.1
        psi_1 = psi_0 + torch.randn(N, dtype=torch.complex64) * 0.001

        # High threshold (more sparse)
        compressor_sparse = DeltaCompressor(sparse_threshold=1e-3)
        compressed_sparse = compressor_sparse.compress(psi_1, psi_0)

        # Low threshold (less sparse)
        compressor_dense = DeltaCompressor(sparse_threshold=1e-8)
        compressed_dense = compressor_dense.compress(psi_1, psi_0)

        # Sparse should be smaller
        assert len(compressed_sparse) < len(compressed_dense)

    def test_compression_ratio(self):
        """Test compression ratio calculation"""
        N = 1000
        compressor = DeltaCompressor()

        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        compressed = compressor.compress(psi)

        original_size = N * 8  # complex64 = 8 bytes
        compressed_size = len(compressed)

        ratio = compressor.get_compression_ratio(original_size, compressed_size)

        assert ratio > 1  # Should achieve compression
        assert ratio < 1000  # Reasonable upper bound

    def test_estimate_size(self):
        """Test size estimation"""
        N = 1000
        compressor = DeltaCompressor()

        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        sizes = compressor.estimate_size(psi)

        assert 'original_bytes' in sizes
        assert 'compressed_bytes' in sizes
        assert 'ratio' in sizes

        assert sizes['original_bytes'] == N * 8
        assert sizes['compressed_bytes'] > 0
        assert sizes['ratio'] > 1

    def test_zero_state(self):
        """Test compression of zero state"""
        N = 1000
        compressor = DeltaCompressor()

        psi = torch.zeros(N, dtype=torch.complex64)

        compressed = compressor.compress(psi)
        psi_recovered = compressor.decompress(compressed)

        # Should be very small (all zeros)
        assert len(compressed) < 1000

        # Should recover zeros
        assert torch.allclose(psi_recovered, torch.zeros_like(psi_recovered), atol=1e-6)

    def test_high_sparsity_compression(self):
        """Test compression with highly sparse delta"""
        N = 10000
        compressor = DeltaCompressor()

        psi_0 = torch.randn(N, dtype=torch.complex64) * 0.1

        # Create sparse delta (only 1% changed)
        psi_1 = psi_0.clone()
        change_indices = torch.randperm(N)[:100]
        psi_1[change_indices] += torch.randn(100, dtype=torch.complex64) * 0.1

        compressed_delta = compressor.compress(psi_1, psi_0)
        compressed_full = compressor.compress(psi_1)

        # Sparse delta should compress much better
        ratio = len(compressed_full) / len(compressed_delta)
        assert ratio > 5  # At least 5x better

    def test_large_scale(self):
        """Test with large state"""
        N = 100000  # 100k nodes
        compressor = DeltaCompressor(quantization_bits=16)

        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        # Should compress without errors
        compressed = compressor.compress(psi)

        # Check compression achieved
        original_size = N * 8
        compression_ratio = original_size / len(compressed)

        assert compression_ratio > 2  # At least 2x compression

    def test_device_handling(self):
        """Test different device handling"""
        N = 1000
        compressor = DeltaCompressor()

        # CPU
        psi_cpu = torch.randn(N, dtype=torch.complex64)
        compressed = compressor.compress(psi_cpu)
        recovered_cpu = compressor.decompress(compressed, device=torch.device('cpu'))

        assert recovered_cpu.device.type == 'cpu'

        # GPU (if available)
        if torch.cuda.is_available():
            psi_gpu = psi_cpu.cuda()
            compressed_gpu = compressor.compress(psi_gpu)
            recovered_gpu = compressor.decompress(compressed_gpu, device=torch.device('cuda'))

            assert recovered_gpu.device.type == 'cuda'

    def test_compression_levels(self):
        """Test different zlib compression levels"""
        N = 1000
        psi = torch.randn(N, dtype=torch.complex64) * 0.1

        sizes = {}

        for level in [1, 6, 9]:
            compressor = DeltaCompressor(compression_level=level)
            compressed = compressor.compress(psi)
            sizes[level] = len(compressed)

        # Higher compression level should give smaller size
        assert sizes[9] <= sizes[6] <= sizes[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
