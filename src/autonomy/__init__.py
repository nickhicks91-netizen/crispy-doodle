"""
Autonomy Layer (v4.2.1)
------------------------
Continuous self-regulating operation for EchoZero.

Fixes from v4.2.0:
- Correct imports (Issue #5 resolved)
- Proper integration
- Thread-safe operation
"""

from .loop import AutonomyEngine

__all__ = ['AutonomyEngine']
