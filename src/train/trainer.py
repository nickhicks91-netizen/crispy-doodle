"""
EchoZero Trainer Loop (v4.2.1)
-------------------------------
Integrates:
- DataStream validation
- HybridForward inference
- CohesionKernel meta-cognition
- EchoMirror Hebbian learning
- Online drift correction

This is the main training orchestrator.

Fixes from v4.2.0:
- Complete integration
- Proper state management
- Drift correction
- φ-modulated learning
"""

import torch
import torch.nn as nn
from typing import Dict, Optional
from ..hybrid import HybridForward, CohesionKernel
from ..core.state import GlobalState
from .echo_mirror import EchoMirrorTrainer
from .datastream import DataStream


class EchoZeroTrainer:
    """
    Main training loop for EchoZero.

    Combines all systems into coherent learning process.
    """

    def __init__(
        self,
        N: int = 64,
        learning_rate: float = 0.001,
        drift_correction: bool = True,
        phi_modulation: bool = True,
        device: Optional[str] = None
    ):
        """
        Args:
            N: Number of ψ nodes
            learning_rate: Hebbian learning rate
            drift_correction: Enable automatic drift correction
            phi_modulation: Modulate learning by φ-depth
            device: Device to place models on
        """
        self.N = N
        self.learning_rate = learning_rate
        self.drift_correction = drift_correction
        self.phi_modulation = phi_modulation
        self.device = device

        # Initialize components
        self.datastream = DataStream(allow_missing=True, device=device)

        input_dim = self.datastream.total_dim
        self.model = HybridForward(N=N, input_dim=input_dim, device=device)

        self.kernel = CohesionKernel(device=device)

        # EchoMirror works on grounding_dim (15)
        grounding_dim = self.datastream.grounding_dim
        self.echo_mirror = EchoMirrorTrainer(
            dim=grounding_dim,
            lr=learning_rate,
            device=device
        )

        # Training statistics
        self.step_count = 0
        self.total_drift_corrections = 0

    def train_step(
        self,
        text_vec: Optional[torch.Tensor] = None,
        vision_vec: Optional[torch.Tensor] = None,
        audio_vec: Optional[torch.Tensor] = None,
        eeg_vec: Optional[torch.Tensor] = None
    ) -> Dict[str, any]:
        """
        Execute one training step.

        Args:
            text_vec, vision_vec, audio_vec, eeg_vec: Multimodal inputs

        Returns:
            Dictionary with training metrics and diagnostics
        """
        self.step_count += 1

        # Step 1: Validate and fuse inputs
        try:
            grounded = self.datastream(text_vec, vision_vec, audio_vec, eeg_vec)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'validation'
            }

        # Step 2: Forward pass through hybrid system
        try:
            hybrid_out = self.model(grounded)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'forward'
            }

        # Step 3: Cohesion Kernel meta-cognition
        try:
            kernel_state = self.kernel(hybrid_out)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'kernel'
            }

        # Step 4: Extract learning signals
        phi = float(hybrid_out['phi'])
        coherence = float(hybrid_out['coherence'].mean())
        drift = float(kernel_state.get('drift', 0.0))
        stress = float(kernel_state.get('stress_level', 0.0))

        # Step 5: Drift correction (if enabled and needed)
        drift_corrected = False
        if self.drift_correction and drift > 0.5:
            self._apply_drift_correction(hybrid_out)
            drift_corrected = True
            self.total_drift_corrections += 1

        # Step 6: Hebbian learning
        # Seed: grounded input
        # Reflection: ψ real part (projected to grounding_dim)
        psi_real = torch.real(hybrid_out['psi'])

        # Project ψ to grounding_dim for EchoMirror
        reflection = self._project_psi_to_grounding(psi_real)

        # Modulate learning strength by φ (if enabled)
        if self.phi_modulation:
            strength = torch.sigmoid(torch.tensor(phi)).item()
        else:
            strength = 1.0

        # EchoMirror update
        echo_info = self.echo_mirror(grounded, reflection, strength)

        # Step 7: Compile training metrics
        metrics = {
            'success': True,
            'step': self.step_count,
            'phi': phi,
            'coherence': coherence,
            'drift': drift,
            'stress': stress,
            'drift_corrected': drift_corrected,
            'learning_strength': strength,
            'echo_mirror': echo_info,
            'meta_stability': float(kernel_state.get('meta_stability', 0.0)),
            'reward': float(kernel_state.get('raw_reward', 0.0))
        }

        return metrics

    def _project_psi_to_grounding(self, psi_real: torch.Tensor) -> torch.Tensor:
        """
        Project ψ (N-dim) to grounding space (grounding_dim).

        Args:
            psi_real: Real part of ψ [N]

        Returns:
            projected: Projected vector [grounding_dim]
        """
        grounding_dim = self.datastream.grounding_dim

        if psi_real.numel() == grounding_dim:
            return psi_real

        elif psi_real.numel() > grounding_dim:
            # Downsample via average pooling
            # Reshape to [grounding_dim, N//grounding_dim] and average
            chunk_size = psi_real.numel() // grounding_dim
            chunks = psi_real[:grounding_dim * chunk_size].view(grounding_dim, chunk_size)
            return chunks.mean(dim=1)

        else:
            # Upsample via linear interpolation
            return torch.nn.functional.interpolate(
                psi_real.unsqueeze(0).unsqueeze(0),
                size=grounding_dim,
                mode='linear',
                align_corners=False
            ).squeeze()

    def _apply_drift_correction(self, hybrid_out: Dict[str, torch.Tensor]):
        """
        Apply drift correction to ψ state.

        Args:
            hybrid_out: Hybrid forward output
        """
        psi = hybrid_out['psi']

        # Simple damping correction
        with GlobalState.write_lock():
            corrected_psi = psi * 0.95
            GlobalState.psi = corrected_psi

    def get_statistics(self) -> Dict[str, any]:
        """Get training statistics."""
        return {
            'total_steps': self.step_count,
            'drift_corrections': self.total_drift_corrections,
            'echo_mirror_strength': self.echo_mirror.get_strength(),
            'echo_mirror_updates': int(self.echo_mirror.update_count)
        }

    def reset(self):
        """Reset trainer state."""
        self.step_count = 0
        self.total_drift_corrections = 0
        self.echo_mirror.reset()
