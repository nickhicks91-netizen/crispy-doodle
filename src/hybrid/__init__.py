"""
Hybrid Integration Layer (v4.2.1)
----------------------------------
Combines EchoZero dynamics with GRCM cognitive modules
and Cohesion Kernel meta-cognitive orchestration.

Fixes from v4.2.0:
- Complete Cohesion Kernel implementation (fixes Issue #4)
- All 20 modules present
- Proper state management
"""

from .forward import HybridForward
from .cohesion_kernel import CohesionKernel

__all__ = ['HybridForward', 'CohesionKernel']
