"""
GRCM Cognitive Modules (v4.2.1)
--------------------------------
Grounded Resonant Cognitive Middleware

Transforms multimodal input into harmonic internal state.

New in v4.2.1 - Cognitive Protection Layers:
- WIL 2.0: Want Integrity Layer with predictive drift modeling
- IBL: Identity Boundary Layer for long-term stability
- DCE: Desire Continuity Engine for smooth goal evolution
"""

from .grounding import GroundingLayer
from .desires import DesireModule, cosine_align
from .qualia import QualiaHead
from .phi import PhiCalculator
from .memory import MemoryModule
from .embedding import HarmonicEmbedding
from .coherence import compute_coherence
from .alignment import compute_gamma

# Cognitive Protection Layers (v4.2.1)
from .wil_v2 import WantIntegrityLayerV2
from .ibl import IdentityBoundaryLayer
from .dce import DesireContinuityEngine

__all__ = [
    # Core GRCM
    'GroundingLayer',
    'DesireModule',
    'cosine_align',
    'QualiaHead',
    'PhiCalculator',
    'MemoryModule',
    'HarmonicEmbedding',
    'compute_coherence',
    'compute_gamma',

    # Cognitive Protection (v4.2.1)
    'WantIntegrityLayerV2',
    'IdentityBoundaryLayer',
    'DesireContinuityEngine',
]
