"""
Device Management for EchoZero
-------------------------------
Handles CPU/GPU allocation, mixed precision, and device migration.
"""

import torch
from typing import Optional
from .errors import DeviceError


class DeviceManager:
    """
    Centralized device management for all tensors.

    Usage:
        dm = DeviceManager()
        tensor = dm.to_device(torch.randn(10))
    """

    def __init__(self, device: Optional[str] = None, use_mixed_precision: bool = False):
        """
        Args:
            device: 'cuda', 'cpu', or None (auto-detect)
            use_mixed_precision: Enable FP16/BF16 for GPU
        """
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'

        self.device = torch.device(device)
        self.use_mixed_precision = use_mixed_precision and device == 'cuda'

        # Scaler for mixed precision
        self.scaler = torch.cuda.amp.GradScaler() if self.use_mixed_precision else None

        print(f"[DeviceManager] Using device: {self.device}")
        if self.use_mixed_precision:
            print("[DeviceManager] Mixed precision enabled")

    def to_device(self, tensor: torch.Tensor) -> torch.Tensor:
        """Move tensor to configured device."""
        try:
            return tensor.to(self.device)
        except Exception as e:
            raise DeviceError(f"Failed to move tensor to {self.device}: {e}")

    def empty_cache(self):
        """Free GPU memory cache."""
        if self.device.type == 'cuda':
            torch.cuda.empty_cache()

    def get_memory_stats(self) -> dict:
        """Get current device memory usage."""
        if self.device.type == 'cuda':
            return {
                'allocated': torch.cuda.memory_allocated(self.device),
                'reserved': torch.cuda.memory_reserved(self.device),
                'max_allocated': torch.cuda.max_memory_allocated(self.device)
            }
        return {}

    def synchronize(self):
        """Synchronize device operations."""
        if self.device.type == 'cuda':
            torch.cuda.synchronize(self.device)


# Global device manager instance
device_manager = DeviceManager()


def to_device(tensor: torch.Tensor) -> torch.Tensor:
    """Convenience function to move tensor to default device."""
    return device_manager.to_device(tensor)
