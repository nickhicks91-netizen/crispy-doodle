"""
Multimodal DataStream (v4.2.1)
-------------------------------
Fuses and validates multimodal input streams.

Input modalities:
- Text embeddings (768-dim)
- Vision embeddings (512-dim, e.g., CLIP)
- Audio features (128-dim, e.g., log-mel)
- EEG/proprioception (64-dim)

Total: 1472-dim → 15-dim grounding

Fixes from v4.2.0 (Issue #9):
- Full dimension validation
- Missing modality handling
- NaN/Inf detection
- Range validation
- Proper error messages
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Optional, Dict
from ..core.errors import ValidationError, DimensionMismatchError


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class DataStream(nn.Module):
    """
    Validated multimodal data stream.

    Ensures all inputs match expected dimensions before fusion.
    """

    def __init__(
        self,
        text_dim: Optional[int] = None,
        vision_dim: Optional[int] = None,
        audio_dim: Optional[int] = None,
        eeg_dim: Optional[int] = None,
        grounding_dim: Optional[int] = None,
        allow_missing: bool = False,
        device: Optional[str] = None
    ):
        """
        Args:
            text_dim: Text embedding dimension (default from config)
            vision_dim: Vision embedding dimension (default from config)
            audio_dim: Audio feature dimension (default from config)
            eeg_dim: EEG/proprioception dimension (default from config)
            grounding_dim: Output grounding dimension (default from config)
            allow_missing: Allow missing modalities (fill with zeros)
            device: Device to place on
        """
        super().__init__()

        # Load dimensions from config
        self.text_dim = text_dim or DIMS['text_dim']
        self.vision_dim = vision_dim or DIMS['vision_dim']
        self.audio_dim = audio_dim or DIMS['audio_dim']
        self.eeg_dim = eeg_dim or DIMS['eeg_dim']
        self.grounding_dim = grounding_dim or DIMS['grounding_dim']

        self.allow_missing = allow_missing

        # Total input dimension
        self.total_dim = self.text_dim + self.vision_dim + self.audio_dim + self.eeg_dim

        # Projection to grounding space
        self.proj = nn.Linear(self.total_dim, self.grounding_dim)

        if device:
            self.to(device)

    def validate_modality(
        self,
        tensor: Optional[torch.Tensor],
        expected_dim: int,
        name: str
    ) -> torch.Tensor:
        """
        Validate a single modality.

        Args:
            tensor: Input tensor (can be None if allow_missing=True)
            expected_dim: Expected dimension
            name: Modality name (for error messages)

        Returns:
            validated: Validated tensor [expected_dim]

        Raises:
            ValidationError: If validation fails
        """
        # Handle missing modality
        if tensor is None:
            if not self.allow_missing:
                raise ValidationError(f"{name} modality is missing (allow_missing=False)")
            return torch.zeros(expected_dim)

        # Check dimensions
        if tensor.numel() != expected_dim:
            raise DimensionMismatchError(
                f"{name} dimension mismatch: expected {expected_dim}, got {tensor.numel()}"
            )

        # Check for NaN/Inf
        if torch.any(torch.isnan(tensor)) or torch.any(torch.isinf(tensor)):
            raise ValidationError(f"{name} contains NaN or Inf values")

        # Check range (embeddings should typically be in reasonable range)
        if torch.abs(tensor).max() > 1000:
            raise ValidationError(
                f"{name} values out of range (max abs value: {torch.abs(tensor).max():.2f})"
            )

        return tensor

    def validate_all(
        self,
        text_vec: Optional[torch.Tensor],
        vision_vec: Optional[torch.Tensor],
        audio_vec: Optional[torch.Tensor],
        eeg_vec: Optional[torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Validate all modalities.

        Returns:
            validated: Dictionary of validated modalities
        """
        return {
            'text': self.validate_modality(text_vec, self.text_dim, 'Text'),
            'vision': self.validate_modality(vision_vec, self.vision_dim, 'Vision'),
            'audio': self.validate_modality(audio_vec, self.audio_dim, 'Audio'),
            'eeg': self.validate_modality(eeg_vec, self.eeg_dim, 'EEG')
        }

    def fuse(self, validated: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Fuse validated modalities.

        Args:
            validated: Dictionary of validated modalities

        Returns:
            fused: Concatenated tensor [total_dim]
        """
        return torch.cat([
            validated['text'],
            validated['vision'],
            validated['audio'],
            validated['eeg']
        ], dim=-1)

    def forward(
        self,
        text_vec: Optional[torch.Tensor] = None,
        vision_vec: Optional[torch.Tensor] = None,
        audio_vec: Optional[torch.Tensor] = None,
        eeg_vec: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Validate, fuse, and project multimodal input.

        Args:
            text_vec: Text embedding [text_dim]
            vision_vec: Vision embedding [vision_dim]
            audio_vec: Audio features [audio_dim]
            eeg_vec: EEG/proprioception [eeg_dim]

        Returns:
            grounded: Grounding vector [grounding_dim]
        """
        # Validate all modalities
        validated = self.validate_all(text_vec, vision_vec, audio_vec, eeg_vec)

        # Fuse
        fused = self.fuse(validated)

        # Project to grounding space
        grounded = self.proj(fused)

        # Apply activation
        grounded = torch.tanh(grounded)

        return grounded

    def get_info(self) -> Dict[str, int]:
        """Get dimension information."""
        return {
            'text_dim': self.text_dim,
            'vision_dim': self.vision_dim,
            'audio_dim': self.audio_dim,
            'eeg_dim': self.eeg_dim,
            'total_dim': self.total_dim,
            'grounding_dim': self.grounding_dim
        }
