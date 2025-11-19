"""
Grounding Layer (v4.2.1)
------------------------
Maps multimodal input → 15-dimensional grounding vector.

Inputs may include:
- Text embeddings
- Audio features (log-mels)
- Visual embeddings (CLIP projected)
- Proprioceptive / sensor data

Fixes from v4.2.0:
- Device management
- Input validation
- Batching support
- Error handling
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Optional
from ..core.errors import DimensionMismatchError, ValidationError
from ..core.device import to_device


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class GroundingLayer(nn.Module):
    """
    Fuses multimodal inputs into unified grounding representation.

    Maps: [text_dim + vision_dim + audio_dim + eeg_dim] → [grounding_dim]
    """

    def __init__(
        self,
        input_dim: Optional[int] = None,
        output_dim: Optional[int] = None,
        device: Optional[str] = None
    ):
        """
        Args:
            input_dim: Total input dimension (default: sum of modalities)
            output_dim: Grounding dimension (default: 15 from config)
            device: Device to place module on
        """
        super().__init__()

        # Default dimensions from config
        if input_dim is None:
            input_dim = (DIMS['text_dim'] + DIMS['vision_dim'] +
                        DIMS['audio_dim'] + DIMS['eeg_dim'])

        self.input_dim = input_dim
        self.output_dim = output_dim or DIMS['grounding_dim']

        # Projection layer
        self.proj = nn.Linear(self.input_dim, self.output_dim)

        # Move to device
        if device:
            self.to(device)

    def validate_input(self, x: torch.Tensor):
        """Validate input dimensions."""
        if x.shape[-1] != self.input_dim:
            raise DimensionMismatchError(
                f"Expected input dim {self.input_dim}, got {x.shape[-1]}"
            )

        if torch.any(torch.isnan(x)) or torch.any(torch.isinf(x)):
            raise ValidationError("Input contains NaN or Inf values")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Project multimodal input to grounding space.

        Args:
            x: Input tensor [batch, input_dim] or [input_dim]

        Returns:
            grounded: Grounding vector [batch, grounding_dim] or [grounding_dim]
        """
        # Handle unbatched input
        unbatched = x.ndim == 1
        if unbatched:
            x = x.unsqueeze(0)

        # Validate
        self.validate_input(x)

        # Project and activate
        grounded = self.proj(x)
        grounded = torch.tanh(grounded)

        # Remove batch dim if input was unbatched
        if unbatched:
            grounded = grounded.squeeze(0)

        return grounded
