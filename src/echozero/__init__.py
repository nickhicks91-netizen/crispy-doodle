"""
EchoZero Core Module
--------------------
Resonant ψ-dynamics engine.
"""

from .dynamics import EchoZeroDynamics
from .coupling import make_ring_coupling, limit_spectral_radius
from .lattice import build_lattice, assign_initial_state
from .ode_solver import rk4_step
from .stability import (
    psi_energy,
    psi_drift,
    coherence_index,
    spectral_stability
)

__all__ = [
    'EchoZeroDynamics',
    'make_ring_coupling',
    'limit_spectral_radius',
    'build_lattice',
    'assign_initial_state',
    'rk4_step',
    'psi_energy',
    'psi_drift',
    'coherence_index',
    'spectral_stability'
]
