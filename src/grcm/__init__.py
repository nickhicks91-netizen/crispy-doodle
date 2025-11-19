"""
GRCM Cognitive Modules (v4.2.1)
--------------------------------
Grounded Resonant Cognitive Middleware

Transforms multimodal input into harmonic internal state.
"""

from .grounding import GroundingLayer
from .desires import DesireModule, cosine_align
from .qualia import QualiaHead
from .phi import PhiCalculator
from .memory import MemoryModule
from .embedding import HarmonicEmbedding
from .coherence import compute_coherence
from .alignment import compute_gamma

__all__ = [
    'GroundingLayer',
    'DesireModule',
    'cosine_align',
    'QualiaHead',
    'PhiCalculator',
    'MemoryModule',
    'HarmonicEmbedding',
    'compute_coherence',
    'compute_gamma'
]
