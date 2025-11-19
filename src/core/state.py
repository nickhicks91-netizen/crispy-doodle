"""
Thread-Safe Global State Management
------------------------------------
Fixes Issues #1 and #2:
- Proper state management (no nn.Parameter for runtime state)
- Thread-safe access with locks
- Atomic read/write operations
- Safe-mode fallback
"""

import torch
import threading
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from contextlib import contextmanager


# Load dimensions
def load_dimensions():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dimensions()


@dataclass
class EchoZeroState:
    """
    Thread-safe state container for EchoZero runtime.

    All mutations must go through atomic operations with locks.
    """
    # Core state
    psi: Optional[torch.Tensor] = None
    memory: Optional[torch.Tensor] = None
    prop_state: Optional[torch.Tensor] = None

    # Metrics
    phi: float = 0.0
    coherence: float = 0.0
    drift: float = 0.0

    # System health
    last_heartbeat: float = 0.0
    safe_mode: bool = False
    error_count: int = 0

    # Configuration
    min_phi: float = 0.1
    max_drift: float = 12.0

    # Lock for thread safety
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def __post_init__(self):
        """Initialize state tensors with correct dimensions."""
        if self.psi is None:
            self.psi = torch.zeros(DIMS['N'], dtype=torch.cfloat)
        if self.memory is None:
            self.memory = torch.zeros(DIMS['memory_dim'])
        if self.prop_state is None:
            self.prop_state = torch.zeros(DIMS['prop_state_dim'])

    # ==================== Thread-Safe Accessors ====================

    @contextmanager
    def read_lock(self):
        """Context manager for safe reads."""
        with self._lock:
            yield self

    @contextmanager
    def write_lock(self):
        """Context manager for safe writes."""
        with self._lock:
            yield self

    def get_psi(self) -> torch.Tensor:
        """Thread-safe read of ψ state."""
        with self._lock:
            return self.psi.clone()

    def set_psi(self, psi: torch.Tensor):
        """Thread-safe atomic write of ψ state."""
        with self._lock:
            if psi.shape != self.psi.shape:
                raise ValueError(f"ψ shape mismatch: expected {self.psi.shape}, got {psi.shape}")
            self.psi = psi.clone()

    def get_memory(self) -> torch.Tensor:
        """Thread-safe read of memory."""
        with self._lock:
            return self.memory.clone()

    def set_memory(self, memory: torch.Tensor):
        """Thread-safe atomic write with clamping."""
        with self._lock:
            if memory.shape != self.memory.shape:
                raise ValueError(f"Memory shape mismatch: expected {self.memory.shape}, got {memory.shape}")
            # Clamp to prevent runaway memory growth
            self.memory = torch.clamp(memory, -10.0, 10.0)

    def get_metrics(self) -> dict:
        """Thread-safe read of all metrics."""
        with self._lock:
            return {
                'phi': self.phi,
                'coherence': self.coherence,
                'drift': self.drift,
                'safe_mode': self.safe_mode,
                'error_count': self.error_count
            }

    def update_metrics(self, phi=None, coherence=None, drift=None):
        """Thread-safe atomic metric update."""
        with self._lock:
            if phi is not None:
                self.phi = float(phi)
            if coherence is not None:
                self.coherence = float(coherence)
            if drift is not None:
                self.drift = float(drift)

    # ==================== Safety ====================

    def activate_safe_mode(self):
        """Puts system into safe fallback mode."""
        with self._lock:
            self.safe_mode = True
            self.psi = torch.zeros_like(self.psi)
            self.prop_state *= 0.5
            self.error_count += 1

    def deactivate_safe_mode(self):
        """Exits safe mode."""
        with self._lock:
            self.safe_mode = False

    def log_error(self, msg: str):
        """Thread-safe error logging."""
        with self._lock:
            self.error_count += 1
            print(f"[EchoZero Error #{self.error_count}] {msg}")

    # ==================== Persistence ====================

    def save_checkpoint(self, path: str):
        """Save state to disk."""
        with self._lock:
            torch.save({
                'psi': self.psi,
                'memory': self.memory,
                'prop_state': self.prop_state,
                'phi': self.phi,
                'coherence': self.coherence,
                'drift': self.drift
            }, path)

    def load_checkpoint(self, path: str):
        """Load state from disk."""
        with self._lock:
            state = torch.load(path)
            self.psi = state['psi']
            self.memory = state['memory']
            self.prop_state = state['prop_state']
            self.phi = state['phi']
            self.coherence = state['coherence']
            self.drift = state['drift']


# Global singleton instance
GlobalState = EchoZeroState()
