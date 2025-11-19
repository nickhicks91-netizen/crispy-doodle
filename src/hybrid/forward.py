"""
Unified Forward Pass for EchoZero + GRCM Hybrid (v4.2.1)
---------------------------------------------------------
Implements EXACT canonical spec with all fixes applied.

Flow:
    grounded = grounding_layer(x)
    freq, I = harmonic_embedding(grounded)
    ψ' = ode_step(dynamics, ψ, I, desires, node_freqs)
    coherence = compute_coherence(ψ, node_freqs)
    qualia = qualia_head(ψ)
    φ = phi_calculator(ψ, coherence, memory, qualia)
    memory' = memory_module(ψ, coherence, memory)
    gamma, align = compute_gamma(freq, desires)

Fixes from v4.2.0:
- State managed via GlobalState (not nn.Parameter)
- Proper I vector broadcasting
- Batching support
- Functional memory updates
- Thread-safe state access
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Dict, Optional

from ..echozero.dynamics import EchoZeroDynamics
from ..echozero.ode_solver import rk4_step
from ..echozero.lattice import build_lattice, assign_initial_state
from ..grcm import (
    GroundingLayer,
    HarmonicEmbedding,
    DesireModule,
    QualiaHead,
    PhiCalculator,
    MemoryModule,
    compute_coherence,
    compute_gamma
)
from ..core.state import GlobalState
from ..core.errors import DimensionMismatchError


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class HybridForward(nn.Module):
    """
    Unified EchoZero + GRCM forward pass.

    Integrates:
    - Multimodal grounding
    - Harmonic embedding
    - ψ-dynamics evolution
    - Cognitive metrics (qualia, φ, coherence)
    - Memory updates
    """

    def __init__(
        self,
        N: Optional[int] = None,
        input_dim: Optional[int] = None,
        device: Optional[str] = None,
        dt: float = 0.01
    ):
        """
        Args:
            N: Number of ψ nodes
            input_dim: Multimodal input dimension
            device: Device to place modules on
            dt: ODE integration time step
        """
        super().__init__()

        self.N = N or DIMS['N']
        self.dt = dt

        # Default input_dim is sum of all modalities
        if input_dim is None:
            input_dim = (DIMS['text_dim'] + DIMS['vision_dim'] +
                        DIMS['audio_dim'] + DIMS['eeg_dim'])

        # GRCM modules
        self.ground = GroundingLayer(input_dim, device=device)
        self.embed = HarmonicEmbedding(N=self.N, device=device)
        self.desires = DesireModule(device=device)
        self.qualia = QualiaHead(N=self.N, device=device)
        self.memory_module = MemoryModule(device=device)
        self.phi_calc = PhiCalculator()

        # EchoZero dynamics
        node_freqs, _ = build_lattice(self.N)
        self.register_buffer('node_freqs', node_freqs)

        omega = torch.linspace(0.5, 2.5, self.N)
        self.dynamics = EchoZeroDynamics(
            N=self.N,
            omega=omega.tolist(),
            device=device
        )

        # Initialize state in GlobalState if not already done
        self._init_global_state()

    def _init_global_state(self):
        """Initialize GlobalState with proper dimensions if needed."""
        with GlobalState.write_lock():
            if GlobalState.psi is None or GlobalState.psi.shape[0] != self.N:
                GlobalState.psi = assign_initial_state(self.N)

            if GlobalState.memory is None or GlobalState.memory.shape[0] != DIMS['memory_dim']:
                GlobalState.memory = self.memory_module.init_memory()

            if GlobalState.prop_state is None or GlobalState.prop_state.shape[0] != DIMS['prop_state_dim']:
                GlobalState.prop_state = torch.zeros(DIMS['prop_state_dim'])

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Execute one forward pass.

        Args:
            x: Multimodal input [input_dim] or [batch, input_dim]

        Returns:
            Dictionary containing:
                - psi: Updated ψ state
                - coherence: Coherence values
                - qualia: Qualia distribution
                - phi: φ-depth
                - memory: Updated memory
                - prop_state: Propagator state
                - align: Alignment values
                - gamma: Gamma modulation
        """
        # Handle batching
        unbatched = x.ndim == 1
        if unbatched:
            x = x.unsqueeze(0)

        batch_size = x.shape[0]

        # Step 1: Grounding
        grounded = self.ground(x)  # [batch, grounding_dim]

        # Step 2: Harmonic embedding
        freq, I = self.embed(grounded)  # freq: [batch, freq_dim], I: [batch, N]

        # Step 3: Get current state (thread-safe)
        with GlobalState.read_lock():
            psi_prev = GlobalState.psi.clone()
            memory_prev = GlobalState.memory.clone()

        # Expand state for batching if needed
        if batch_size > 1:
            psi_prev = psi_prev.unsqueeze(0).repeat(batch_size, 1)
            memory_prev = memory_prev.unsqueeze(0).repeat(batch_size, 1)

        # Step 4: Get desires
        desires = self.desires()  # [desire_dim]

        # Step 5: Evolve ψ
        psi_new = rk4_step(
            self.dynamics,
            psi_prev,
            self.dt,
            I,
            desires,
            self.node_freqs
        )  # [batch, N] or [N]

        # Step 6: Compute coherence
        coherence = compute_coherence(psi_new, self.node_freqs)  # [batch, N]

        # Step 7: Compute qualia
        qualia = self.qualia(psi_new)  # [batch, 4]

        # Step 8: Update memory
        memory_new = self.memory_module(psi_new, coherence, memory_prev)  # [batch, memory_dim]

        # Step 9: Compute φ
        phi = self.phi_calc(psi_new, coherence, memory_new, qualia)  # [batch] or scalar

        # Step 10: Compute alignment and gamma
        gamma, align = compute_gamma(freq, desires)  # [batch] or scalar

        # Step 11: Update propagator state (simple integration)
        force = align.mean(dim=-1 if align.ndim > 1 else 0) * qualia[..., 1]  # Use 'alert' channel

        # Read current prop_state
        with GlobalState.read_lock():
            prop_state = GlobalState.prop_state.clone()

        # Update with force
        if batch_size == 1 and unbatched:
            prop_state = prop_state + force * self.dt
        else:
            prop_state = prop_state + force.mean() * self.dt  # Average over batch

        # Step 12: Write updated state back (thread-safe)
        if batch_size == 1:
            # Single sample: update GlobalState
            psi_to_save = psi_new.squeeze(0) if psi_new.ndim == 2 else psi_new
            memory_to_save = memory_new.squeeze(0) if memory_new.ndim == 2 else memory_new

            with GlobalState.write_lock():
                GlobalState.psi = psi_to_save
                GlobalState.memory = memory_to_save
                GlobalState.prop_state = prop_state

        # Prepare output
        output = {
            'psi': psi_new,
            'coherence': coherence,
            'qualia': qualia,
            'phi': phi,
            'memory': memory_new,
            'prop_state': prop_state,
            'align': align,
            'gamma': gamma,
            'freq': freq
        }

        # Remove batch dimension if input was unbatched
        if unbatched:
            for key in output:
                if isinstance(output[key], torch.Tensor) and output[key].ndim > 1 and output[key].shape[0] == 1:
                    output[key] = output[key].squeeze(0)

        return output
