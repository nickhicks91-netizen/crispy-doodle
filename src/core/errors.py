"""
EchoZero Exception Hierarchy
-----------------------------
Structured error handling for all modules.
"""


class EchoZeroError(Exception):
    """Base exception for all EchoZero errors."""
    pass


class StateCorruptionError(EchoZeroError):
    """Raised when ψ or memory state becomes corrupted."""
    pass


class DimensionMismatchError(EchoZeroError):
    """Raised when tensor dimensions don't match expectations."""
    pass


class ConvergenceError(EchoZeroError):
    """Raised when ODE integration fails to converge."""
    pass


class SyncError(EchoZeroError):
    """Raised when distributed synchronization fails."""
    pass


class ValidationError(EchoZeroError):
    """Raised when input validation fails."""
    pass


class DeviceError(EchoZeroError):
    """Raised when device (CPU/GPU) operations fail."""
    pass


class SecurityError(EchoZeroError):
    """Raised when security checks fail."""
    pass
