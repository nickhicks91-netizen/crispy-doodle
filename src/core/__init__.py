"""
EchoZero Core Infrastructure (v4.2.1)
--------------------------------------
Thread-safe state management, device handling, and error hierarchy.
"""

from .state import EchoZeroState, GlobalState
from .errors import (
    EchoZeroError,
    StateCorruptionError,
    DimensionMismatchError,
    ConvergenceError,
    SyncError,
    ValidationError,
    DeviceError,
    SecurityError
)
from .device import DeviceManager, device_manager, to_device

__all__ = [
    'EchoZeroState',
    'GlobalState',
    'EchoZeroError',
    'StateCorruptionError',
    'DimensionMismatchError',
    'ConvergenceError',
    'SyncError',
    'ValidationError',
    'DeviceError',
    'SecurityError',
    'DeviceManager',
    'device_manager',
    'to_device'
]
