"""
Training System (v4.2.1)
-------------------------
Hebbian learning for EchoZero without backpropagation.

Components:
- EchoMirror: Hebbian resonance trainer
- DataStream: Validated multimodal fusion
- Trainer: Main training orchestrator

Fixes from v4.2.0:
- Complete implementation
- DataStream validation (Issue #9 resolved)
- Drift correction
- φ-modulated learning
"""

from .echo_mirror import EchoMirrorTrainer
from .datastream import DataStream
from .trainer import EchoZeroTrainer

__all__ = [
    'EchoMirrorTrainer',
    'DataStream',
    'EchoZeroTrainer'
]
