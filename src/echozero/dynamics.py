"""
EchoZero ψ-Dynamics (v4.2.1 - Corrected)
-----------------------------------------
Implements the core resonant state evolution equation:

    ψ̇ = (-α + iω) ψ + K ψ - β |ψ|^2 ψ + γ ψ + I(t) - λ Σ_j ψ_j

Fixes from v4.2.0:
- Uses register_buffer instead of nn.Parameter for K matrix
- Proper device management
- Dimension validation
- Error handling
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from ..core.errors import DimensionMismatchError
from ..core.device import to_device


# Load dimensions
def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class EchoZeroDynamics(nn.Module):
    """
    EchoZero continuous-time ODE dynamics.

    Computes ψ̇ given instantaneous state and drive inputs.
    """

    def __init__(
        self,
        N: int = None,
        omega: float = 1.5,
        alpha: float = 0.10,
        beta: float = 0.05,
        lam: float = 0.02,
        device: str = None
    ):
        """
        Args:
            N: Number of nodes (default from config)
            omega: Base frequency
            alpha: Damping coefficient
            beta: Nonlinear suppression
            lam: Hub suppression
            device: 'cuda' or 'cpu'
        """
        super().__init__()

        self.N = N or DIMS['N']
        self.alpha = alpha
        self.beta = beta
        self.lam = lam

        # ω may be scalar or per-node vector
        if isinstance(omega, (int, float)):
            omega_tensor = torch.full((self.N,), omega, dtype=torch.float32)
        else:
            omega_tensor = torch.tensor(omega, dtype=torch.float32)

        # Use register_buffer for non-learnable state
        self.register_buffer('omega', omega_tensor)

        # K is N×N complex coupling matrix (stored as real/imag components)
        K_real = torch.randn(self.N, self.N) * 0.01
        K_imag = torch.randn(self.N, self.N) * 0.01

        self.register_buffer('K_real', K_real)
        self.register_buffer('K_imag', K_imag)

        # Move to device
        if device:
            self.to(device)

    def K(self) -> torch.Tensor:
        """Get complex coupling matrix."""
        return torch.complex(self.K_real, self.K_imag)

    def forward(
        self,
        psi: torch.Tensor,
        I_t: torch.Tensor,
        desires: torch.Tensor,
        node_freqs: torch.Tensor
    ) -> torch.Tensor:
        """
        Computes ψ̇ given instantaneous state and drive inputs.

        Args:
            psi: Complex state [N] or [batch, N]
            I_t: External drive [N] or [batch, N]
            desires: Desire vector [desire_dim]
            node_freqs: Node frequencies [N]

        Returns:
            dpsi_dt: Time derivative [N] or [batch, N]
        """
        # Validate dimensions
        if psi.shape[-1] != self.N:
            raise DimensionMismatchError(
                f"psi has wrong size: expected [..., {self.N}], got {psi.shape}"
            )

        # Handle batching
        is_batched = psi.ndim == 2
        if not is_batched:
            psi = psi.unsqueeze(0)
            I_t = I_t.unsqueeze(0)

        batch_size = psi.shape[0]

        # Get coupling matrix
        K = self.K()

        # Core linear term: (-α + iω) ψ
        damping_freq = -self.alpha + 1j * self.omega
        local = damping_freq * psi

        # Harmonic coupling: K ψ
        coupled = torch.matmul(psi, K.T)  # [batch, N]

        # Nonlinear suppression: -β |ψ|^2 ψ
        psi_mag_sq = torch.abs(psi) ** 2
        nonlinear = -self.beta * psi_mag_sq * psi

        # Desire alignment modulation
        # align = cos(Re(ψ)) · desires
        psi_real = torch.real(psi)
        align = torch.cos(psi_real).mean(dim=-1, keepdim=True)  # [batch, 1]

        # γ = 0.2 + 0.4 * sigmoid(align)
        gamma = 0.2 + 0.4 * torch.sigmoid(align)
        want = gamma * psi

        # External drive
        drive = I_t

        # Global hub suppression: -λ Σ ψ
        hub_sum = torch.sum(psi, dim=-1, keepdim=True)  # [batch, 1]
        hub = -self.lam * hub_sum

        # Total derivative
        dpsi_dt = local + coupled + nonlinear + want + drive + hub

        # Remove batch dimension if input was unbatched
        if not is_batched:
            dpsi_dt = dpsi_dt.squeeze(0)

        return dpsi_dt
