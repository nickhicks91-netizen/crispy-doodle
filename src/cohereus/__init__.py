"""
CO-HERE-US — National Financial Stability System

Built using EchoZero v4.2.1 "DNA":
- Risk Harmonization Layer (RHL) ← WIL 2.0
- Strategy Identity Layer (SIL) ← IBL
- Position Smoothing Engine (PSE) ← DCE
- Account Orchestrator ← Distributed mesh
- Harmonic Optimizer ← ψ-dynamics (simplified)
- Inter-Bot Diversity ← Coherence (inverted)
- Torus Grid ← Edge-free topology
- PLF 1.0 & 2.0 ← Predictive coherence
- Fracton Mode ← Constrained mobility

Version: 1.5.0 (PLF 2.0 + Fracton Mode integrated)
EchoZero DNA Source: v4.2.1
"""

from .core.risk_harmonization import RiskHarmonizationLayer
from .core.strategy_identity import StrategyIdentityLayer
from .core.position_smoothing import PositionSmoothingEngine
from .core.torus_grid import TorusGrid
from .core.phase_locked_fracton import PhaseLockedFractonLayer, PLFConfig

from .orchestration.account_orchestrator import AccountOrchestrator, CohortState
from .orchestration.torus_orchestrator import TorusCohortOrchestrator, TorusOrchestratorConfig
from .orchestration.diversity_system import InterBotDiversitySystem

from .optimizer.harmonic_optimizer import HarmonicOptimizer

from .plf2 import PLF2Controller
from .fracton import FractonModeController
from .integration import PLF2Pipeline, FullPipeline

__all__ = [
    # Core protection layers
    'RiskHarmonizationLayer',
    'StrategyIdentityLayer',
    'PositionSmoothingEngine',
    'TorusGrid',
    'PhaseLockedFractonLayer',
    'PLFConfig',

    # Orchestration
    'AccountOrchestrator',
    'CohortState',
    'TorusCohortOrchestrator',
    'TorusOrchestratorConfig',
    'InterBotDiversitySystem',

    # Optimization
    'HarmonicOptimizer',

    # PLF 2.0 & Fracton Mode
    'PLF2Controller',
    'FractonModeController',

    # Integrated Pipelines
    'PLF2Pipeline',
    'FullPipeline',
]

__version__ = "1.5.0"
__echozero_version__ = "4.2.1"
