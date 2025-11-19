"""
Harmonic Variational Memory (v4.2.1)
-------------------------------------
Variational compression of memory for efficient long-term storage.

Uses variational autoencoder-like architecture to:
- Compress memory to latent representation
- Preserve harmonic structure
- Enable efficient retrieval
- Reduce memory footprint

Fixes from v4.2.0:
- Proper state management
- Efficient compression
"""

import torch
import torch.nn as nn
from typing import Dict, Optional, Tuple


class HarmonicVariationalMemory(nn.Module):
    """
    Variational compression for long-term memory.
    """

    def __init__(
        self,
        memory_dim: int = 128,
        latent_dim: int = 32,
        device: Optional[str] = None
    ):
        """
        Args:
            memory_dim: Full memory dimension
            latent_dim: Compressed latent dimension
            device: Device to place on
        """
        super().__init__()

        self.memory_dim = memory_dim
        self.latent_dim = latent_dim

        # Encoder: memory → (μ, σ)
        self.encoder_mean = nn.Sequential(
            nn.Linear(memory_dim, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim)
        )

        self.encoder_logvar = nn.Sequential(
            nn.Linear(memory_dim, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim)
        )

        # Decoder: latent → memory
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, memory_dim),
            nn.Tanh()
        )

        if device:
            self.to(device)

    def encode(self, memory: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode memory to latent distribution.

        Args:
            memory: Memory vector [memory_dim]

        Returns:
            mean: Latent mean [latent_dim]
            logvar: Latent log-variance [latent_dim]
        """
        # Ensure size
        if memory.numel() > self.memory_dim:
            memory = memory[:self.memory_dim]
        elif memory.numel() < self.memory_dim:
            memory = torch.nn.functional.pad(memory, (0, self.memory_dim - memory.numel()))

        mean = self.encoder_mean(memory)
        logvar = self.encoder_logvar(memory)

        return mean, logvar

    def reparameterize(self, mean: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """
        Reparameterization trick for sampling.

        Args:
            mean: Latent mean
            logvar: Latent log-variance

        Returns:
            z: Sampled latent vector
        """
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        z = mean + eps * std
        return z

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """
        Decode latent to memory.

        Args:
            z: Latent vector [latent_dim]

        Returns:
            reconstructed: Reconstructed memory [memory_dim]
        """
        reconstructed = self.decoder(z)
        return reconstructed

    def compress(self, memory: torch.Tensor) -> torch.Tensor:
        """
        Compress memory to latent representation (deterministic).

        Args:
            memory: Memory vector

        Returns:
            latent: Compressed representation
        """
        mean, _ = self.encode(memory)
        return mean  # Use mean for deterministic compression

    def decompress(self, latent: torch.Tensor) -> torch.Tensor:
        """
        Decompress latent to memory.

        Args:
            latent: Compressed representation

        Returns:
            memory: Decompressed memory
        """
        return self.decode(latent)

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Compress and reconstruct memory.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output (optional)

        Returns:
            Dictionary with compressed_memory, reconstruction
        """
        # Get memory from state or hybrid_out
        if hybrid_out is not None and 'memory' in hybrid_out:
            memory = hybrid_out['memory']
        else:
            memory = state.get('memory', torch.zeros(self.memory_dim))

        # Encode
        mean, logvar = self.encode(memory)

        # Sample latent
        z = self.reparameterize(mean, logvar)

        # Decode
        reconstructed = self.decode(z)

        # Compute reconstruction error
        recon_error = torch.mean((memory - reconstructed) ** 2)

        # Compute KL divergence
        kl_div = -0.5 * torch.sum(1 + logvar - mean.pow(2) - logvar.exp())

        return {
            'compressed_memory': z,
            'memory_reconstruction': reconstructed,
            'reconstruction_error': recon_error,
            'kl_divergence': kl_div,
            'compression_ratio': self.memory_dim / self.latent_dim
        }
