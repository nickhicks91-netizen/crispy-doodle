"""
CO-HERE-US Core Protection Layers

Adapted from EchoZero cognitive protection layers:
- RHL: Risk Harmonization Layer (from WIL 2.0)
- SIL: Strategy Identity Layer (from IBL)
- PSE: Position Smoothing Engine (from DCE)
- TorusGrid: Edge-free topology for cohort placement
- PLF: Phase-Locked Fracton stability layer
"""

from .risk_harmonization import RiskHarmonizationLayer
from .strategy_identity import StrategyIdentityLayer
from .position_smoothing import PositionSmoothingEngine
from .torus_grid import TorusGrid
from .phase_locked_fracton import PhaseLockedFractonLayer, PLFConfig

__all__ = [
    'RiskHarmonizationLayer',
    'StrategyIdentityLayer',
    'PositionSmoothingEngine',
    'TorusGrid',
    'PhaseLockedFractonLayer',
    'PLFConfig',
]
