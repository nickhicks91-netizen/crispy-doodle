"""
Torus Cohort Orchestrator — National-Scale Account Management

Manages cohorts on torus topology with:
- Phase-based rebalancing schedules
- PLF damping integration
- Shell-based temporal diversity
- Coordinated account management

DNA Source: EchoZero distributed mesh + node coordination patterns
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from typing import Dict, Any, Optional, Callable
from ..core.torus_grid import TorusGrid
from ..core.phase_locked_fracton import PhaseLockedFractonLayer, PLFConfig


@dataclass
class TorusOrchestratorConfig:
    """
    Controls cohort layout and rebalance sequencing.
    """
    grid_w: int = 4
    grid_h: int = 3                      # 4x3 = 12 cohorts default
    shell_rebalance_frac: float = 0.25   # Fraction of shells rebalanced per cycle
    activity_floor: float = 1e-4         # Minimum activity level
    phase_noise: float = 0.03            # Phase jitter to avoid perfect locks
    plf_config: Optional[PLFConfig] = None


class TorusCohortOrchestrator:
    """
    National-scale cohort orchestrator on torus topology.

    Manages:
    - Cohort placement on torus grid
    - Phase-based rebalancing schedules
    - PLF damping modulation
    - Activity tracking

    Required hooks (supplied by caller):
      - optimizer_step(cohort_id, damping_mod, context) -> target_weights
      - apply_weights(cohort_id, weights, context) -> None

    Example:
        def optimizer_step(cohort_id, damping_mod, context):
            # Apply damping to your RHL/PSE/HOE
            context["rhl"].set_damping(damping_mod)
            weights = context["optimizer"].compute_target(...)
            return weights

        def apply_weights(cohort_id, weights, context):
            context["cohort_states"][cohort_id]["weights"] = weights

        orchestrator = TorusCohortOrchestrator(
            optimizer_step=optimizer_step,
            apply_weights=apply_weights
        )
    """

    def __init__(
        self,
        config: Optional[TorusOrchestratorConfig] = None,
        optimizer_step: Optional[Callable[[int, float, Dict[str, Any]], np.ndarray]] = None,
        apply_weights: Optional[Callable[[int, np.ndarray, Dict[str, Any]], None]] = None,
    ):
        """
        Initialize torus orchestrator.

        Args:
            config: Orchestrator configuration
            optimizer_step: Hook for computing target weights
            apply_weights: Hook for applying weights to cohort
        """
        self.cfg = config or TorusOrchestratorConfig()
        self.grid = TorusGrid(self.cfg.grid_w, self.cfg.grid_h)
        self.plf = PhaseLockedFractonLayer(
            self.grid,
            config=self.cfg.plf_config
        )

        self.optimizer_step = optimizer_step
        self.apply_weights = apply_weights

        # Persistent cohort state
        self.cohort_phase = np.zeros(self.grid.size, dtype=np.float32)
        self.cohort_activity = np.ones(self.grid.size, dtype=np.float32) * self.cfg.activity_floor

        self.cycle = 0

    def _update_activity(self, cohort_returns: np.ndarray):
        """
        Update activity proxy from returns.

        Activity = abs(return) + floor
        High activity → high rebalancing pressure

        Args:
            cohort_returns: Realized returns for each cohort
        """
        act = np.abs(cohort_returns).astype(np.float32) + self.cfg.activity_floor
        self.cohort_activity = act

    def _update_phase(self, cohort_returns: np.ndarray):
        """
        Update phase proxy from returns.

        Phase = angle of return relative to mean
        Used for coherence detection

        Args:
            cohort_returns: Realized returns for each cohort
        """
        r = cohort_returns.astype(np.float32)
        mu = float(np.mean(r))
        sigma = float(np.std(r)) + 1e-6

        # Arctangent phase encoding
        phase = np.arctan2((r - mu), sigma)

        # Add light noise to prevent perfect locks
        phase += np.random.normal(0, self.cfg.phase_noise, size=phase.shape)

        self.cohort_phase = np.clip(phase, -np.pi, np.pi)

    def _shell_schedule(self) -> np.ndarray:
        """
        Determine which cohorts to rebalance this cycle using shell-based scheduling.

        Uses concentric rings from torus center to spread rebalancing
        temporally across the grid.

        Returns:
            Array of cohort IDs to rebalance
        """
        center = (self.cfg.grid_w // 2, self.cfg.grid_h // 2)
        max_r = max(self.cfg.grid_w, self.cfg.grid_h)

        # Collect shells (concentric rings)
        shells = []
        for r in range(max_r):
            ring = list(self.grid.ring_walk(center, r))
            ids = [self.grid.index(x, y) for x, y in ring]
            shells.append(np.unique(ids))

        # Select fraction of shells, rotating each cycle
        n_shells = len(shells)
        k = max(1, int(np.ceil(n_shells * self.cfg.shell_rebalance_frac)))
        start = self.cycle % n_shells

        chosen = []
        for i in range(k):
            chosen.append(shells[(start + i) % n_shells])

        return np.unique(np.concatenate(chosen))

    def tick(
        self,
        cohort_returns: np.ndarray,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute one orchestrator cycle (typically yearly).

        Args:
            cohort_returns: Realized blended returns for each cohort
            context: Optional data passed to optimizer/apply hooks

        Returns:
            Dictionary containing:
            - cycle: Current cycle number
            - rebalance_ids: Cohorts rebalanced this cycle
            - plf: PLF output (phase_map, fracton_density, damping_mods)
            - targets: Target weights per rebalanced cohort
        """
        context = context or {}
        self.cycle += 1

        # Update cohort state from returns
        self._update_activity(cohort_returns)
        self._update_phase(cohort_returns)

        # Run PLF stabilization
        plf_out = self.plf.step(self.cohort_phase, self.cohort_activity)
        damping_mods = plf_out["damping_mods"]

        # Determine rebalancing schedule
        rebalance_ids = self._shell_schedule()

        # Execute rebalancing with PLF-modulated damping
        if self.optimizer_step is None or self.apply_weights is None:
            raise ValueError("optimizer_step and apply_weights hooks must be provided.")

        targets = {}
        for cid in rebalance_ids:
            mod = float(damping_mods[cid])
            w = self.optimizer_step(cid, mod, context)
            self.apply_weights(cid, w, context)
            targets[cid] = w

        return {
            "cycle": self.cycle,
            "rebalance_ids": rebalance_ids,
            "plf": plf_out,
            "targets": targets
        }

    def get_state(self) -> Dict[str, Any]:
        """
        Get current orchestrator state for monitoring/debugging.

        Returns:
            Dictionary with phase, activity, and cycle information
        """
        return {
            "cycle": self.cycle,
            "cohort_phase": self.cohort_phase.copy(),
            "cohort_activity": self.cohort_activity.copy(),
            "grid_size": self.grid.size,
        }

    def reset(self):
        """Reset orchestrator state."""
        self.cohort_phase = np.zeros(self.grid.size, dtype=np.float32)
        self.cohort_activity = np.ones(self.grid.size, dtype=np.float32) * self.cfg.activity_floor
        self.cycle = 0
        self.plf.reset()


# Example usage and validation
if __name__ == "__main__":
    print("Testing Torus Cohort Orchestrator...")

    # Define hooks
    called = {"step": 0, "apply": 0}

    def optimizer_step(cid, mod, ctx):
        called["step"] += 1
        # Return dummy 5-asset weights
        return np.ones(5) / 5.0

    def apply_weights(cid, w, ctx):
        called["apply"] += 1

    # Create orchestrator
    orchestrator = TorusCohortOrchestrator(
        optimizer_step=optimizer_step,
        apply_weights=apply_weights
    )

    print(f"\n1. Initial state:")
    state = orchestrator.get_state()
    print(f"  Grid size: {state['grid_size']}")
    print(f"  Cycle: {state['cycle']}")

    # Simulate 10 cycles
    print(f"\n2. Running 10 cycles:")
    for i in range(10):
        # Random returns
        returns = np.random.randn(12) * 0.02

        out = orchestrator.tick(returns)

        if i % 3 == 0:
            print(f"  Cycle {out['cycle']}: "
                  f"{len(out['rebalance_ids'])} cohorts rebalanced, "
                  f"avg damping mod = {out['plf']['damping_mods'].mean():.3f}")

    print(f"\n3. Hook invocations:")
    print(f"  optimizer_step called: {called['step']} times")
    print(f"  apply_weights called: {called['apply']} times")
    print(f"  (Should be equal)")

    print(f"\n✓ Torus Orchestrator operational")
