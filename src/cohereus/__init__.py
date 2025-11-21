"""
CO-HERE-US — National Financial Stability System

Built using EchoZero v4.2.1 "DNA":
- Risk Harmonization Layer (RHL) ← WIL 2.0
- Strategy Identity Layer (SIL) ← IBL
- Position Smoothing Engine (PSE) ← DCE
- Account Orchestrator ← Distributed mesh
- Harmonic Optimizer ← ψ-dynamics (simplified)
- Inter-Bot Diversity ← Coherence (inverted)

Version: 1.0.0
EchoZero DNA Source: v4.2.1
"""

from .core.risk_harmonization import RiskHarmonizationLayer
from .core.strategy_identity import StrategyIdentityLayer
from .core.position_smoothing import PositionSmoothingEngine
from .orchestration.account_orchestrator import AccountOrchestrator, CohortState
from .orchestration.diversity_system import InterBotDiversitySystem
from .optimizer.harmonic_optimizer import HarmonicOptimizer

__all__ = [
    # Core protection layers
    'RiskHarmonizationLayer',
    'StrategyIdentityLayer',
    'PositionSmoothingEngine',

    # Orchestration
    'AccountOrchestrator',
    'CohortState',
    'InterBotDiversitySystem',

    # Optimization
    'HarmonicOptimizer',
]

__version__ = "1.0.0"
__echozero_version__ = "4.2.1"
