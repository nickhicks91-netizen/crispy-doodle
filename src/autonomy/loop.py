"""
Autonomy Loop (v4.2.1)
-----------------------
Continuous self-regulating operation for EchoZero.

Responsibilities:
- Continual EchoMirror learning
- Drift monitoring + correction
- φ-feedback stabilization
- Challenge-based adaptation
- Memory consolidation cycles
- Safety thresholds
- Heartbeat + logging

Fixes from v4.2.0 (Issue #5):
- Correct imports (HybridForward, not forward function)
- Proper integration with all systems
- Thread-safe operation
- Clean shutdown
"""

import time
import threading
from typing import Optional, Dict
import torch

from ..hybrid import HybridForward, CohesionKernel
from ..train import EchoZeroTrainer
from ..core.state import GlobalState
from ..core.errors import EchoZeroError


class AutonomyEngine:
    """
    Self-regulating continuous operation engine.

    Runs in background thread, constantly:
    - Processing inputs (or generating synthetic baseline)
    - Updating ψ state
    - Learning via EchoMirror
    - Correcting drift
    - Consolidating memory
    """

    def __init__(
        self,
        N: int = 64,
        dt: float = 0.1,
        drift_threshold: float = 0.5,
        phi_min: float = 0.1,
        device: Optional[str] = None
    ):
        """
        Args:
            N: Number of ψ nodes
            dt: Time step for each tick
            drift_threshold: Maximum acceptable drift
            phi_min: Minimum acceptable φ-depth
            device: Device to run on
        """
        self.N = N
        self.dt = dt
        self.drift_threshold = drift_threshold
        self.phi_min = phi_min
        self.device = device

        # Initialize systems
        self.trainer = EchoZeroTrainer(N=N, device=device)

        # State
        self.tick_count = 0
        self.running = False
        self.thread = None

        # Statistics
        self.stats = {
            'total_ticks': 0,
            'drift_corrections': 0,
            'safe_mode_activations': 0,
            'consolidations': 0,
            'errors': 0
        }

    def _generate_baseline_input(self) -> Dict[str, torch.Tensor]:
        """
        Generate synthetic baseline input when no external input available.

        Returns:
            Dictionary with text, vision, audio, eeg tensors
        """
        return {
            'text_vec': torch.randn(768) * 0.01,
            'vision_vec': torch.randn(512) * 0.01,
            'audio_vec': torch.randn(128) * 0.01,
            'eeg_vec': torch.randn(64) * 0.01
        }

    def tick(self):
        """Execute one autonomy loop tick."""
        try:
            # Generate or retrieve input
            input_data = self._generate_baseline_input()

            # Train step (includes forward pass, kernel, and learning)
            metrics = self.trainer.train_step(**input_data)

            if not metrics['success']:
                GlobalState.log_error(f"Train step failed: {metrics.get('error', 'unknown')}")
                self.stats['errors'] += 1
                return

            # Extract metrics
            phi = metrics['phi']
            drift = metrics['drift']
            stress = metrics['stress']

            # Drift correction (if needed beyond trainer's automatic correction)
            if drift > self.drift_threshold and not metrics['drift_corrected']:
                self._apply_drift_correction()
                self.stats['drift_corrections'] += 1

            # φ stabilization
            if phi < self.phi_min:
                GlobalState.activate_safe_mode()
                self.stats['safe_mode_activations'] += 1

            # Memory consolidation (every 500 ticks or if high stress)
            if (self.tick_count % 500 == 0) or (stress > 0.7):
                self._consolidate_memory()
                self.stats['consolidations'] += 1

            # Update statistics
            self.stats['total_ticks'] += 1

            # Heartbeat
            with GlobalState.write_lock():
                GlobalState.last_heartbeat = time.time()

        except Exception as e:
            GlobalState.log_error(f"Autonomy tick error: {e}")
            self.stats['errors'] += 1

            # Activate safe mode on repeated errors
            if self.stats['errors'] > 10:
                GlobalState.activate_safe_mode()

    def _apply_drift_correction(self):
        """Apply emergency drift correction."""
        with GlobalState.write_lock():
            if GlobalState.psi is not None:
                GlobalState.psi = GlobalState.psi * 0.90  # Dampen

    def _consolidate_memory(self):
        """Trigger memory consolidation."""
        # This is handled by the CohesionKernel's consolidation module
        # Just log it here
        pass

    def run(self):
        """
        Main autonomy loop (runs in thread).

        Continues until stop() is called.
        """
        self.running = True

        while self.running:
            try:
                self.tick()
                self.tick_count += 1
                time.sleep(self.dt)

            except KeyboardInterrupt:
                self.stop()
                break

            except Exception as e:
                GlobalState.log_error(f"Autonomy loop error: {e}")
                # Continue running even on error
                time.sleep(self.dt)

    def start(self):
        """Start autonomy loop in background thread."""
        if self.running:
            print("[Autonomy] Already running")
            return

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

        print(f"[Autonomy] Started (dt={self.dt}s)")

    def stop(self):
        """Stop autonomy loop."""
        self.running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        print("[Autonomy] Stopped")

    def get_statistics(self) -> Dict[str, int]:
        """Get autonomy statistics."""
        return {
            **self.stats,
            'tick_count': self.tick_count,
            'trainer_steps': self.trainer.step_count
        }
