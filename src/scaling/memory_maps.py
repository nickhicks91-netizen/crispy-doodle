"""
Memory Excitation Maps
Efficient tracking of memory activation patterns in large lattices
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Dict, List
from collections import deque


class MemoryExcitationMap(nn.Module):
    """
    Tracks and visualizes memory excitation patterns

    Features:
    - Spatial activity maps
    - Temporal tracking (history)
    - Hotspot detection
    - Efficient storage for large N
    """

    def __init__(
        self,
        N: int,
        history_length: int = 100,
        resolution: int = 100,
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize memory excitation map

        Args:
            N: Lattice size
            history_length: Number of timesteps to track
            resolution: Spatial resolution (downsampled from N)
            device: Computation device
        """
        super().__init__()

        self.N = N
        self.history_length = history_length
        self.resolution = min(resolution, N)  # Can't exceed N
        self.device = device

        # Calculate downsampling factor
        self.downsample_factor = max(1, N // self.resolution)

        # History buffer (circular)
        self.history = deque(maxlen=history_length)

        # Cumulative statistics
        self.register_buffer(
            'cumulative_activation',
            torch.zeros(self.resolution, device=device)
        )
        self.register_buffer(
            'peak_activation',
            torch.zeros(self.resolution, device=device)
        )
        self.activation_count = 0

    def update(self, psi: torch.Tensor, memory: Optional[torch.Tensor] = None):
        """
        Update excitation map with new state

        Args:
            psi: Complex tensor [batch, N] or [N]
            memory: Optional memory state [batch, memory_dim] or [memory_dim]
        """
        # Handle batching (use first batch element for tracking)
        if psi.dim() == 2:
            psi = psi[0]

        # Calculate activation (magnitude)
        activation = torch.abs(psi)

        # Downsample if needed
        if self.downsample_factor > 1:
            activation_downsampled = self._downsample(activation)
        else:
            activation_downsampled = activation

        # Update statistics
        self.cumulative_activation += activation_downsampled
        self.peak_activation = torch.maximum(self.peak_activation, activation_downsampled)
        self.activation_count += 1

        # Add to history
        self.history.append(activation_downsampled.cpu())

    def _downsample(self, activation: torch.Tensor) -> torch.Tensor:
        """Downsample activation to resolution"""
        # Average pooling
        activation_np = activation.cpu().numpy()
        downsampled = []

        for i in range(self.resolution):
            start = i * self.downsample_factor
            end = min(start + self.downsample_factor, self.N)
            region_mean = activation_np[start:end].mean()
            downsampled.append(region_mean)

        return torch.tensor(downsampled, device=self.device)

    def get_current_map(self) -> torch.Tensor:
        """Get current excitation map"""
        if len(self.history) == 0:
            return torch.zeros(self.resolution, device=self.device)
        return self.history[-1].to(self.device)

    def get_average_map(self) -> torch.Tensor:
        """Get time-averaged excitation map"""
        if self.activation_count == 0:
            return torch.zeros(self.resolution, device=self.device)
        return self.cumulative_activation / self.activation_count

    def get_peak_map(self) -> torch.Tensor:
        """Get peak excitation map"""
        return self.peak_activation

    def detect_hotspots(self, threshold: float = 0.8) -> List[int]:
        """
        Detect hotspot regions

        Args:
            threshold: Activation threshold (relative to peak)

        Returns:
            List of hotspot indices
        """
        avg_map = self.get_average_map()
        max_activation = avg_map.max()

        if max_activation == 0:
            return []

        # Normalize
        normalized = avg_map / max_activation

        # Find hotspots
        hotspots = torch.where(normalized > threshold)[0]

        # Convert to original indices
        original_indices = []
        for idx in hotspots:
            start = idx.item() * self.downsample_factor
            end = min(start + self.downsample_factor, self.N)
            original_indices.extend(range(start, end))

        return original_indices

    def get_temporal_pattern(self, region_idx: int, window: int = 50) -> np.ndarray:
        """
        Get temporal activation pattern for a region

        Args:
            region_idx: Region index (in downsampled space)
            window: Lookback window

        Returns:
            Temporal pattern array
        """
        if region_idx >= self.resolution:
            raise ValueError(f"Region index {region_idx} out of range")

        # Extract from history
        pattern = []
        history_list = list(self.history)[-window:]

        for h in history_list:
            pattern.append(h[region_idx].item())

        return np.array(pattern)

    def get_spatial_distribution(self) -> Dict[str, torch.Tensor]:
        """Get spatial distribution statistics"""
        avg_map = self.get_average_map()

        return {
            'mean': avg_map,
            'std': torch.std(avg_map),
            'max': avg_map.max(),
            'min': avg_map.min(),
            'entropy': self._compute_entropy(avg_map)
        }

    def _compute_entropy(self, distribution: torch.Tensor) -> torch.Tensor:
        """Compute entropy of distribution"""
        # Normalize to probability distribution
        total = distribution.sum()
        if total == 0:
            return torch.tensor(0.0, device=self.device)

        prob = distribution / total

        # Remove zeros
        prob = prob[prob > 0]

        # Compute entropy
        entropy = -torch.sum(prob * torch.log(prob))

        return entropy

    def reset(self):
        """Reset all tracking"""
        self.history.clear()
        self.cumulative_activation.zero_()
        self.peak_activation.zero_()
        self.activation_count = 0

    def get_stats(self) -> Dict:
        """Get tracking statistics"""
        return {
            'N': self.N,
            'resolution': self.resolution,
            'downsample_factor': self.downsample_factor,
            'history_length': len(self.history),
            'max_history': self.history_length,
            'activation_count': self.activation_count,
            'current_mean': self.get_current_map().mean().item() if len(self.history) > 0 else 0,
            'average_mean': self.get_average_map().mean().item(),
            'peak_max': self.peak_activation.max().item()
        }


# Example usage
if __name__ == "__main__":
    # Test with large lattice
    N = 100000
    resolution = 1000

    print(f"Testing memory excitation map with N={N:,} nodes...")
    print(f"Resolution: {resolution}")

    excitation_map = MemoryExcitationMap(
        N=N,
        history_length=100,
        resolution=resolution
    )

    # Simulate some activations
    print(f"\nSimulating activations...")
    for t in range(50):
        # Create activation with hotspot
        psi = torch.randn(N, dtype=torch.complex64) * 0.01

        # Add hotspot around center
        center = N // 2
        hotspot_size = N // 10
        psi[center:center+hotspot_size] += torch.randn(hotspot_size, dtype=torch.complex64) * 0.1

        excitation_map.update(psi)

    # Get statistics
    stats = excitation_map.get_stats()
    print(f"\nExcitation map statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.6f}")
        else:
            print(f"  {key}: {value}")

    # Detect hotspots
    hotspots = excitation_map.detect_hotspots(threshold=0.7)
    print(f"\nHotspots detected:")
    print(f"  Count: {len(hotspots)}")
    if hotspots:
        print(f"  First few: {hotspots[:10]}")

    # Temporal pattern
    region_idx = resolution // 2  # Center region
    pattern = excitation_map.get_temporal_pattern(region_idx, window=30)
    print(f"\nTemporal pattern (region {region_idx}):")
    print(f"  Mean: {pattern.mean():.6f}")
    print(f"  Std: {pattern.std():.6f}")
    print(f"  Trend: {'increasing' if pattern[-1] > pattern[0] else 'decreasing'}")

    # Spatial distribution
    spatial = excitation_map.get_spatial_distribution()
    print(f"\nSpatial distribution:")
    print(f"  Mean: {spatial['mean'].mean():.6f}")
    print(f"  Std: {spatial['std']:.6f}")
    print(f"  Entropy: {spatial['entropy']:.4f}")

    print("\n✓ Memory excitation map tests passed")
