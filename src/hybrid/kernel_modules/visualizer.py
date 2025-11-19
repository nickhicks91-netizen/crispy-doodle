"""
Harmonic State Visualizer (v4.2.1)
-----------------------------------
Generates visualizable representations of system state.

Outputs:
- ψ-state projections (2D/3D)
- Coherence heatmaps
- φ-depth timeseries
- Qualia distributions
- Memory activation patterns
- Stability indicators

Not meant for real-time rendering, but for:
- Debugging
- Analysis
- Logging
- Dashboard generation

Fixes from v4.2.0:
- Proper state management
- Efficient projection algorithms
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class HarmonicStateVisualizer(nn.Module):
    """
    State visualization and projection.
    """

    def __init__(
        self,
        projection_dim: int = 2,
        device: Optional[str] = None
    ):
        """
        Args:
            projection_dim: Dimension for ψ projection (2 or 3)
            device: Device to place on
        """
        super().__init__()

        self.projection_dim = projection_dim

        # ψ-state projector: N-dimensional ψ → 2D/3D
        self.psi_projector = nn.Linear(64, projection_dim)  # Assumes N=64

        # Memory projector
        self.memory_projector = nn.Linear(128, projection_dim)

        if device:
            self.to(device)

    def project_psi(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Project ψ to low-dimensional space.

        Args:
            psi: Complex ψ state [N] or [batch, N]

        Returns:
            projection: 2D/3D projection [projection_dim] or [batch, projection_dim]
        """
        # Use real part
        psi_real = torch.real(psi)

        # Handle size mismatch
        if psi_real.shape[-1] != 64:
            if psi_real.shape[-1] > 64:
                psi_real = psi_real[..., :64]
            else:
                psi_real = torch.nn.functional.pad(psi_real, (0, 64 - psi_real.shape[-1]))

        # Project
        projection = self.psi_projector(psi_real)

        return projection

    def project_memory(self, memory: torch.Tensor) -> torch.Tensor:
        """
        Project memory to low-dimensional space.

        Args:
            memory: Memory vector [memory_dim] or [batch, memory_dim]

        Returns:
            projection: 2D/3D projection
        """
        # Handle size
        if memory.shape[-1] > 128:
            memory = memory[..., :128]
        elif memory.shape[-1] < 128:
            memory = torch.nn.functional.pad(memory, (0, 128 - memory.shape[-1]))

        # Project
        projection = self.memory_projector(memory)

        return projection

    def compute_coherence_heatmap(self, coherence: torch.Tensor) -> torch.Tensor:
        """
        Generate coherence heatmap.

        Args:
            coherence: Coherence values [N] or [batch, N]

        Returns:
            heatmap: Reshaped coherence for visualization
        """
        # Reshape to 2D grid (8x8 for N=64)
        N = coherence.shape[-1]
        grid_size = int(N ** 0.5)

        if N != grid_size ** 2:
            # Pad to perfect square
            target_size = (grid_size + 1) ** 2
            coherence = torch.nn.functional.pad(coherence, (0, target_size - N))
            grid_size += 1

        heatmap = coherence.reshape(*coherence.shape[:-1], grid_size, grid_size)

        return heatmap

    def compute_qualia_bars(self, qualia: torch.Tensor) -> torch.Tensor:
        """
        Generate qualia bar chart data.

        Args:
            qualia: Qualia distribution [4] or [batch, 4]

        Returns:
            bars: Normalized qualia values
        """
        # Ensure 4 channels
        if qualia.shape[-1] < 4:
            qualia = torch.nn.functional.pad(qualia, (0, 4 - qualia.shape[-1]))

        # Normalize
        bars = qualia / (qualia.sum(dim=-1, keepdim=True) + 1e-8)

        return bars

    def compute_memory_activation(self, memory: torch.Tensor) -> torch.Tensor:
        """
        Generate memory activation pattern.

        Args:
            memory: Memory vector

        Returns:
            activation: Activation levels [memory_dim]
        """
        # Normalize to [0, 1]
        activation = torch.sigmoid(memory)

        return activation

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Generate all visualizations.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with all visualization data
        """
        psi = hybrid_out['psi']
        coherence = hybrid_out['coherence']
        qualia = hybrid_out['qualia']
        memory = hybrid_out['memory']
        phi = hybrid_out['phi']

        # Generate visualizations
        psi_projection = self.project_psi(psi)
        memory_projection = self.project_memory(memory)
        coherence_heatmap = self.compute_coherence_heatmap(coherence)
        qualia_bars = self.compute_qualia_bars(qualia)
        memory_activation = self.compute_memory_activation(memory)

        # φ timeseries (just return current value, external system tracks history)
        phi_current = phi.mean() if phi.numel() > 1 else phi

        return {
            'psi_projection': psi_projection,
            'memory_projection': memory_projection,
            'coherence_heatmap': coherence_heatmap,
            'qualia_bars': qualia_bars,
            'memory_activation': memory_activation,
            'phi_current': phi_current,
            'visualization_ready': True
        }
