"""
CO-HERE-US Core Components (Unity Version)

- TorusGrid: Edge-free topology for cohort placement
- PLF Lite: Phase-Locked Fracton stability layer (soft protection only)
"""

from .torus_grid import TorusGrid
from .phase_locked_fracton import PhaseLockedFractonLayer, PLFConfig

__all__ = [
    'TorusGrid',
    'PhaseLockedFractonLayer',
    'PLFConfig',
]
