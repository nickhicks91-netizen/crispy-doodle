"""
World Model+ (v4.2.1)
---------------------
Maintains a predictive model of system behavior and environment state.

Learns patterns in:
- ψ-state evolution
- Coherence trajectories
- Qualia transitions
- External input patterns

Fixes from v4.2.0:
- Proper state management
- Batching support
- Device management
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Dict, Optional


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class WorldModelPlus(nn.Module):
    """
    Predictive world model tracking system dynamics.
    """

    def __init__(
        self,
        state_dim: Optional[int] = None,
        hidden_dim: int = 64,
        device: Optional[str] = None
    ):
        """
        Args:
            state_dim: Dimension of world state (default: world_model_dim from config)
            hidden_dim: Hidden dimension for prediction network
            device: Device to place on
        """
        super().__init__()

        self.state_dim = state_dim or DIMS.get('world_model_dim', 32)
        self.hidden_dim = hidden_dim

        # Prediction network: state_t → state_{t+1}
        self.predictor = nn.Sequential(
            nn.Linear(self.state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, self.state_dim),
            nn.Tanh()
        )

        # State encoder: hybrid_output → world_state
        self.encoder = nn.Linear(DIMS['N'] + DIMS['qualia_dim'] + 1, self.state_dim)

        if device:
            self.to(device)

    def encode_state(self, hybrid_out: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Encode hybrid output into world state representation.

        Args:
            hybrid_out: Dictionary with psi, qualia, phi, coherence, etc.

        Returns:
            world_state: Encoded state [state_dim] or [batch, state_dim]
        """
        psi = hybrid_out['psi']
        qualia = hybrid_out['qualia']
        phi = hybrid_out['phi']
        coherence = hybrid_out['coherence']

        # Handle batching
        unbatched = psi.ndim == 1
        if unbatched:
            psi = psi.unsqueeze(0)
            qualia = qualia.unsqueeze(0)
            if phi.ndim == 0:
                phi = phi.unsqueeze(0)
            coherence = coherence.unsqueeze(0)

        # Aggregate ψ (take real part and mean)
        psi_real = torch.real(psi)
        psi_agg = psi_real.mean(dim=-1, keepdim=True)  # [batch, 1]

        # Aggregate coherence
        coh_agg = coherence.mean(dim=-1, keepdim=True)  # [batch, 1]

        # Concatenate features
        features = torch.cat([psi_real, qualia, phi.unsqueeze(-1) if phi.ndim == 1 else phi], dim=-1)

        # Encode
        world_state = self.encoder(features)

        if unbatched:
            world_state = world_state.squeeze(0)

        return world_state

    def predict_next(self, current_state: torch.Tensor) -> torch.Tensor:
        """
        Predict next world state.

        Args:
            current_state: Current world state [state_dim] or [batch, state_dim]

        Returns:
            next_state: Predicted next state
        """
        return self.predictor(current_state)

    def forward(self, hybrid_out: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Encode current state and predict next.

        Args:
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with world_state and world_prediction
        """
        world_state = self.encode_state(hybrid_out)
        world_pred = self.predict_next(world_state)

        return {
            'world_state': world_state,
            'world_prediction': world_pred
        }
