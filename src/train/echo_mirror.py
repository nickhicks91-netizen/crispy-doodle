"""
EchoMirror Trainer (v4.2.1)
----------------------------
Hebbian learning mechanism for EchoZero.

Canonical update rule:
    ΔW = η * (seed_vector ⊗ reflection_vector)

Where:
- seed_vector = grounded input or harmonic embedding
- reflection_vector = system's ψ response (real projection)
- η = learning rate

This is NOT backpropagation. This is pure Hebbian strengthening.

Fixes from v4.2.0:
- Proper state management
- Device support
- Batching support
- Drift correction integration
"""

import torch
import torch.nn as nn
from typing import Optional, Dict


class EchoMirrorTrainer(nn.Module):
    """
    Hebbian resonance strengthening for EchoZero.

    The EchoMirror learns by reinforcing patterns that produce
    high φ-depth and coherence, without gradient descent.
    """

    def __init__(
        self,
        dim: int,
        lr: float = 0.001,
        decay: float = 0.9999,
        device: Optional[str] = None
    ):
        """
        Args:
            dim: Dimension of vectors to learn
            lr: Hebbian learning rate
            decay: Weight decay (prevents runaway growth)
            device: Device to place on
        """
        super().__init__()

        self.dim = dim
        self.lr = lr
        self.decay = decay

        # Resonance memory matrix (accumulates outer products)
        # Use buffer (not Parameter) since updates are manual
        self.register_buffer('W', torch.zeros(dim, dim))

        # Update counter
        self.register_buffer('update_count', torch.tensor(0))

        if device:
            self.to(device)

    def hebbian_update(
        self,
        seed_vec: torch.Tensor,
        reflection_vec: torch.Tensor,
        strength: float = 1.0
    ):
        """
        Perform Hebbian update: ΔW = η * strength * (seed ⊗ reflection)

        Args:
            seed_vec: Input vector [dim]
            reflection_vec: Output vector [dim]
            strength: Modulation factor (e.g., based on φ or coherence)
        """
        # Ensure vectors are correct size
        if seed_vec.numel() != self.dim or reflection_vec.numel() != self.dim:
            # Pad or truncate
            seed_vec = self._adjust_size(seed_vec)
            reflection_vec = self._adjust_size(reflection_vec)

        # Compute outer product
        delta = torch.outer(seed_vec, reflection_vec)

        # Apply Hebbian update (no gradients)
        with torch.no_grad():
            # Decay existing weights slightly
            self.W *= self.decay

            # Add new association
            self.W += self.lr * strength * delta

            # Increment counter
            self.update_count += 1

    def _adjust_size(self, vec: torch.Tensor) -> torch.Tensor:
        """Adjust vector to match dim."""
        if vec.numel() > self.dim:
            return vec[:self.dim]
        elif vec.numel() < self.dim:
            return torch.nn.functional.pad(vec, (0, self.dim - vec.numel()))
        return vec

    def recall(self, seed_vec: torch.Tensor) -> torch.Tensor:
        """
        Recall associated pattern.

        Args:
            seed_vec: Input vector

        Returns:
            recalled: Associated pattern from memory
        """
        seed_vec = self._adjust_size(seed_vec)
        recalled = torch.matmul(self.W, seed_vec)
        return recalled

    def get_strength(self) -> float:
        """Get current memory strength (Frobenius norm)."""
        return float(torch.norm(self.W))

    def reset(self):
        """Reset memory matrix."""
        with torch.no_grad():
            self.W.zero_()
            self.update_count.zero_()

    def forward(
        self,
        seed_vec: torch.Tensor,
        reflection_vec: torch.Tensor,
        strength: Optional[float] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Perform Hebbian update and return diagnostics.

        Args:
            seed_vec: Input vector
            reflection_vec: Output vector
            strength: Optional strength modulation

        Returns:
            Dictionary with update info
        """
        if strength is None:
            strength = 1.0

        # Store pre-update norm
        pre_norm = self.get_strength()

        # Update
        self.hebbian_update(seed_vec, reflection_vec, strength)

        # Post-update norm
        post_norm = self.get_strength()

        return {
            'pre_norm': pre_norm,
            'post_norm': post_norm,
            'update_count': int(self.update_count),
            'memory_growth': post_norm - pre_norm
        }
