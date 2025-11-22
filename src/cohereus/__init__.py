"""
CO-HERE-US — National Financial Stability System (Unity Version)

Built using EchoZero v4.2.1 "DNA":
- Torus Grid ← Edge-free topology
- PLF Lite ← Soft protection (no return suppression)
- Account Orchestrator ← Distributed mesh
- Harmonic Optimizer ← ψ-dynamics (simplified)
- Inter-Bot Diversity ← Coherence (inverted)
- Transparency Layer ← User-facing observability
- Fairness Layer ← Contribution caps only

Unity Version: Preserves $72k-74k outcome with annual averaging.
All over-aggressive dampening layers removed.

Version: 1.0.0 (Unity)
EchoZero DNA Source: v4.2.1
"""

from .core.torus_grid import TorusGrid
from .core.phase_locked_fracton import PhaseLockedFractonLayer, PLFConfig

from .orchestration.account_orchestrator import AccountOrchestrator, CohortState
from .orchestration.torus_orchestrator import TorusCohortOrchestrator, TorusOrchestratorConfig
from .orchestration.diversity_system import InterBotDiversitySystem

from .optimizer.harmonic_optimizer import HarmonicOptimizer

from .transparency import (
    MetricsDashboard,
    DriftCurveTracker,
    ContributionTracker,
    ProjectionVisualizer,
)

from .fairness import (
    ContributionCap,
    CapConfig,
)

__all__ = [
    # Core topology
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

    # Transparency Layer
    'MetricsDashboard',
    'DriftCurveTracker',
    'ContributionTracker',
    'ProjectionVisualizer',

    # Fairness Layer (Caps Only)
    'ContributionCap',
    'CapConfig',
]

__version__ = "1.0.0"
__echozero_version__ = "4.2.1"
