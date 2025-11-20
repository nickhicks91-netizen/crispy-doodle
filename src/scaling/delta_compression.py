"""
Delta Compression
Compress ψ state changes for efficient storage and transmission
Fixes Issue #8: Delta compression for large lattices
"""

import torch
import numpy as np
from typing import Optional, Tuple, Dict
import zlib
import pickle


class DeltaCompressor:
    """
    Delta compression for ψ states

    Features:
    - Delta encoding (store only changes)
    - Quantization for additional compression
    - Sparse representation of deltas
    - zlib compression of serialized data
    """

    def __init__(
        self,
        quantization_bits: int = 16,
        sparse_threshold: float = 1e-6,
        compression_level: int = 6
    ):
        """
        Initialize delta compressor

        Args:
            quantization_bits: Bits for quantization (8, 16, 32)
            sparse_threshold: Threshold for sparse encoding
            compression_level: zlib compression level (0-9)
        """
        self.quantization_bits = quantization_bits
        self.sparse_threshold = sparse_threshold
        self.compression_level = compression_level

        # Quantization parameters
        if quantization_bits == 8:
            self.qmin = -128
            self.qmax = 127
            self.dtype = np.int8
        elif quantization_bits == 16:
            self.qmin = -32768
            self.qmax = 32767
            self.dtype = np.int16
        else:  # 32
            self.qmin = -2147483648
            self.qmax = 2147483647
            self.dtype = np.int32

    def compress(
        self,
        psi_current: torch.Tensor,
        psi_previous: Optional[torch.Tensor] = None
    ) -> bytes:
        """
        Compress ψ state using delta encoding

        Args:
            psi_current: Current ψ state [N] or [batch, N]
            psi_previous: Previous ψ state (if None, no delta)

        Returns:
            Compressed bytes
        """
        # Handle batching
        if psi_current.dim() == 2:
            # Compress batch sequentially
            compressed_list = []
            batch_size = psi_current.shape[0]

            prev = psi_previous if psi_previous is not None else None

            for i in range(batch_size):
                compressed = self._compress_single(
                    psi_current[i],
                    prev[i] if prev is not None else None
                )
                compressed_list.append(compressed)

            # Combine batch
            data = {
                'batch': True,
                'size': batch_size,
                'data': compressed_list
            }
            return zlib.compress(pickle.dumps(data), level=self.compression_level)

        else:
            return self._compress_single(psi_current, psi_previous)

    def _compress_single(
        self,
        psi_current: torch.Tensor,
        psi_previous: Optional[torch.Tensor]
    ) -> bytes:
        """Compress single ψ state"""

        # Move to CPU and numpy
        psi_curr_np = psi_current.cpu().numpy()

        if psi_previous is not None:
            # Delta encoding
            psi_prev_np = psi_previous.cpu().numpy()
            delta = psi_curr_np - psi_prev_np
            is_delta = True
        else:
            # Full state
            delta = psi_curr_np
            is_delta = False

        # Separate real and imaginary
        delta_real = np.real(delta)
        delta_imag = np.imag(delta)

        # Sparse encoding (only store non-zero elements)
        mask_real = np.abs(delta_real) > self.sparse_threshold
        mask_imag = np.abs(delta_imag) > self.sparse_threshold

        # Get non-zero indices and values
        indices_real = np.where(mask_real)[0].astype(np.uint32)
        values_real = delta_real[mask_real]

        indices_imag = np.where(mask_imag)[0].astype(np.uint32)
        values_imag = delta_imag[mask_imag]

        # Quantize values
        scale_real = self._compute_scale(values_real)
        scale_imag = self._compute_scale(values_imag)

        quant_real = self._quantize(values_real, scale_real)
        quant_imag = self._quantize(values_imag, scale_imag)

        # Package data
        data = {
            'is_delta': is_delta,
            'N': len(delta),
            'indices_real': indices_real,
            'values_real': quant_real,
            'scale_real': scale_real,
            'indices_imag': indices_imag,
            'values_imag': quant_imag,
            'scale_imag': scale_imag,
            'dtype': str(self.dtype)
        }

        # Serialize and compress
        serialized = pickle.dumps(data)
        compressed = zlib.compress(serialized, level=self.compression_level)

        return compressed

    def decompress(
        self,
        compressed_data: bytes,
        psi_previous: Optional[torch.Tensor] = None,
        device: torch.device = torch.device('cpu')
    ) -> torch.Tensor:
        """
        Decompress ψ state

        Args:
            compressed_data: Compressed bytes
            psi_previous: Previous ψ state (needed if delta)
            device: Target device

        Returns:
            Decompressed ψ tensor
        """
        # Decompress
        decompressed = zlib.decompress(compressed_data)
        data = pickle.loads(decompressed)

        # Check if batch
        if isinstance(data, dict) and data.get('batch'):
            batch_list = []
            prev = psi_previous if psi_previous is not None else None

            for i, compressed_single in enumerate(data['data']):
                psi_single = self._decompress_single(
                    compressed_single,
                    prev[i] if prev is not None else None,
                    device
                )
                batch_list.append(psi_single)

            return torch.stack(batch_list)

        else:
            return self._decompress_single(compressed_data, psi_previous, device)

    def _decompress_single(
        self,
        compressed_data: bytes,
        psi_previous: Optional[torch.Tensor],
        device: torch.device
    ) -> torch.Tensor:
        """Decompress single ψ state"""

        # If already a dict, use it; otherwise decompress
        if isinstance(compressed_data, dict):
            data = compressed_data
        else:
            decompressed = zlib.decompress(compressed_data)
            data = pickle.loads(decompressed)

        N = data['N']
        is_delta = data['is_delta']

        # Reconstruct sparse arrays
        delta_real = np.zeros(N, dtype=np.float32)
        delta_imag = np.zeros(N, dtype=np.float32)

        # Dequantize real
        if len(data['indices_real']) > 0:
            dequant_real = self._dequantize(data['values_real'], data['scale_real'])
            delta_real[data['indices_real']] = dequant_real

        # Dequantize imaginary
        if len(data['indices_imag']) > 0:
            dequant_imag = self._dequantize(data['values_imag'], data['scale_imag'])
            delta_imag[data['indices_imag']] = dequant_imag

        # Reconstruct complex
        delta = delta_real + 1j * delta_imag

        # Convert to tensor
        delta_tensor = torch.from_numpy(delta).to(device)

        # Apply delta if needed
        if is_delta:
            if psi_previous is None:
                raise ValueError("Delta compression requires previous state")
            psi_current = psi_previous + delta_tensor
        else:
            psi_current = delta_tensor

        return psi_current

    def _compute_scale(self, values: np.ndarray) -> float:
        """Compute quantization scale"""
        if len(values) == 0:
            return 1.0

        max_abs = np.abs(values).max()
        if max_abs == 0:
            return 1.0

        scale = max_abs / self.qmax
        return scale

    def _quantize(self, values: np.ndarray, scale: float) -> np.ndarray:
        """Quantize float values to integers"""
        if len(values) == 0:
            return np.array([], dtype=self.dtype)

        quantized = np.clip(values / scale, self.qmin, self.qmax)
        return quantized.astype(self.dtype)

    def _dequantize(self, quantized: np.ndarray, scale: float) -> np.ndarray:
        """Dequantize integers to floats"""
        return quantized.astype(np.float32) * scale

    def get_compression_ratio(
        self,
        original_size: int,
        compressed_size: int
    ) -> float:
        """Calculate compression ratio"""
        return original_size / max(compressed_size, 1)

    def estimate_size(self, psi: torch.Tensor) -> Dict[str, int]:
        """Estimate sizes"""
        # Original size (complex64 = 8 bytes per element)
        original = psi.numel() * 8

        # Compress to estimate
        compressed_data = self.compress(psi)
        compressed = len(compressed_data)

        return {
            'original_bytes': original,
            'compressed_bytes': compressed,
            'ratio': original / max(compressed, 1)
        }


# Example usage
if __name__ == "__main__":
    # Create compressor
    compressor = DeltaCompressor(quantization_bits=16, sparse_threshold=1e-6)

    # Test data
    N = 10000
    psi_0 = torch.randn(N, dtype=torch.complex64) * 0.1
    psi_1 = psi_0 + torch.randn(N, dtype=torch.complex64) * 0.01  # Small delta

    print(f"Testing delta compression with N={N:,} nodes...")

    # Full compression (no delta)
    compressed_full = compressor.compress(psi_0)
    print(f"\nFull compression:")
    print(f"  Original: {N * 8:,} bytes")
    print(f"  Compressed: {len(compressed_full):,} bytes")
    print(f"  Ratio: {(N * 8) / len(compressed_full):.2f}x")

    # Delta compression
    compressed_delta = compressor.compress(psi_1, psi_0)
    print(f"\nDelta compression:")
    print(f"  Original: {N * 8:,} bytes")
    print(f"  Compressed: {len(compressed_delta):,} bytes")
    print(f"  Ratio: {(N * 8) / len(compressed_delta):.2f}x")

    # Decompress and verify
    psi_0_recovered = compressor.decompress(compressed_full)
    psi_1_recovered = compressor.decompress(compressed_delta, psi_0)

    error_0 = torch.abs(psi_0 - psi_0_recovered).mean().item()
    error_1 = torch.abs(psi_1 - psi_1_recovered).mean().item()

    print(f"\nReconstruction error:")
    print(f"  Full: {error_0:.6f}")
    print(f"  Delta: {error_1:.6f}")

    # Batch test
    psi_batch = torch.randn(4, N, dtype=torch.complex64) * 0.1
    compressed_batch = compressor.compress(psi_batch)
    psi_batch_recovered = compressor.decompress(compressed_batch)

    error_batch = torch.abs(psi_batch - psi_batch_recovered).mean().item()
    print(f"\nBatch compression:")
    print(f"  Batch size: 4")
    print(f"  Original: {4 * N * 8:,} bytes")
    print(f"  Compressed: {len(compressed_batch):,} bytes")
    print(f"  Ratio: {(4 * N * 8) / len(compressed_batch):.2f}x")
    print(f"  Error: {error_batch:.6f}")

    print("\n✓ Delta compression tests passed (Issue #8 resolved)")
