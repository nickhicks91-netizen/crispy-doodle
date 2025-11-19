"""
Cohesion Kernel Modules (v4.2.1)
---------------------------------
All 20 meta-cognitive modules for EchoZero orchestration.

Fixes from v4.2.0:
- All modules now fully implemented (fixes Issue #4)
- Proper state management
- Batching support
- Device management
"""

from .world_model import WorldModelPlus
from .memory_plus import MemoryPlus
from .curriculum import CurriculumEngine
from .tool_arbitration import ToolArbitration
from .predictive_routing import PredictiveGoalRouting
from .context_windows import ContextWindows
from .identity_encoding import IdentityEncoding
from .meta_coherence import MetaCoherenceBalancer
from .drift_monitor import DriftMonitor
from .stress_detector import LatentStressDetector
from .episodic_memory import EpisodicMemory
from .rehearsal import WorkingMemoryRehearsal
from .predictive_attention import PredictiveAttention
from .tool_policies import ContextualToolPolicies
from .scenario_generator import ScenarioGenerator
from .consolidation import MemoryConsolidation
from .variational_memory import HarmonicVariationalMemory
from .meta_stability import MetaStabilityAnalyzer
from .reward_model import HarmonicRewardModel
from .visualizer import HarmonicStateVisualizer

__all__ = [
    'WorldModelPlus',
    'MemoryPlus',
    'CurriculumEngine',
    'ToolArbitration',
    'PredictiveGoalRouting',
    'ContextWindows',
    'IdentityEncoding',
    'MetaCoherenceBalancer',
    'DriftMonitor',
    'LatentStressDetector',
    'EpisodicMemory',
    'WorkingMemoryRehearsal',
    'PredictiveAttention',
    'ContextualToolPolicies',
    'ScenarioGenerator',
    'MemoryConsolidation',
    'HarmonicVariationalMemory',
    'MetaStabilityAnalyzer',
    'HarmonicRewardModel',
    'HarmonicStateVisualizer'
]
