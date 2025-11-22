"""
Phase-Locked Fracton Layer (PLF 1.0) — Base Stability Layer

Meta-damping modulator that produces:
- phase_map: Cohort phase coherence per cell
- fracton_density: Cluster strength per cell
- damping_mods: Recommended damping multipliers for upstream layers

Does not directly modify trades or allocations. Feeds risk harmonization,
position smoothing, and diversity systems.

DNA Source: Adapted from EchoZero's coherence calculations (inverted for diversity)
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from typing import Dict, Optional
from .torus_grid import TorusGrid


@dataclass
class PLFConfig:
    """
    Controls strength and timescales of PLF stabilization.

    Parameters control the tradeoff between:
    - Responsiveness (higher smoothing = slower adaptation)
    - Stability (higher gains = stronger modulation)
    """

    phase_smoothing: float = 0.15      # EMA for phase stability
    density_smoothing: float = 0.10    # EMA for fracton density
    locking_gain: float = 0.35         # Phase coherence → damping strength
    cluster_gain: float = 0.25         # Density → damping strength
    min_mod: float = 0.70              # Floor multiplier (prevents over-damping)
    max_mod: float = 1.30              # Ceiling multiplier (prevents instability)
    eps: float = 1e-8                  # Numerical stability constant


class PhaseLockedFractonLayer:
    """
    PLF 1.0 — Phase-Locked Fracton Stability Layer

    Operates on cohort-level state (not per-account).
    Computes meta-stability signals that upstream layers use to
    modulate their damping parameters.

    Inputs (per rebalance cycle):
      - cohort_phases: (num_cells,) float in [-pi, pi]
      - cohort_activity: (num_cells,) float >= 0 (rebalance pressure)

    Outputs:
      - phase_map: Phase coherence field
      - fracton_density: Cluster density field
      - damping_mods: Recommended damping multipliers

    DNA Source: EchoZero coherence → phase diversity
    """

    def __init__(self, grid: TorusGrid, config: Optional[PLFConfig] = None):
        """
        Initialize PLF layer.

        Args:
            grid: Torus grid topology
            config: PLF configuration parameters
        """
        self.grid = grid
        self.cfg = config or PLFConfig()

        # Persistent EMA state
        self._phase_ema = np.zeros(grid.size, dtype=np.float32)
        self._density_ema = np.zeros(grid.size, dtype=np.float32)

    def _phase_coherence(self, phases: np.ndarray) -> np.ndarray:
        """
        Compute phase coherence using local neighborhood.

        Coherence = magnitude of mean unit phasor in 8-neighbor region.
        High coherence → neighbors are synchronizing → increase damping.

        Args:
            phases: Phase angles [-pi, pi] for each cohort

        Returns:
            Coherence values [0, 1] for each cohort
        """
        coh = np.zeros_like(phases, dtype=np.float32)

        for idx in range(self.grid.size):
            x, y = self.grid.coords(idx)
            neigh = self.grid.neighbors8(x, y)
            neigh_idx = [self.grid.index(nx, ny) for nx, ny in neigh]

            # Local phase angles
            local = phases[neigh_idx]

            # Mean phasor (complex unit vector)
            phasor = np.exp(1j * local)
            coh[idx] = np.abs(np.mean(phasor))

        return coh

    def _fracton_density(self, activity: np.ndarray) -> np.ndarray:
        """
        Compute fracton density (local clustering of activity).

        High density = activity is concentrated relative to neighbors.
        This indicates cluster formation → increase damping to prevent
        synchronized movement.

        Args:
            activity: Activity level (rebalance pressure) per cohort

        Returns:
            Density values [0, 1] for each cohort
        """
        dens = np.zeros_like(activity, dtype=np.float32)

        for idx in range(self.grid.size):
            x, y = self.grid.coords(idx)
            neigh = self.grid.neighbors8(x, y)
            neigh_idx = [self.grid.index(nx, ny) for nx, ny in neigh]

            # Local activity
            local = activity[neigh_idx]
            mu = float(np.mean(local))
            sigma = float(np.std(local)) + self.cfg.eps

            # Z-score (how much this cell deviates from neighbors)
            dens[idx] = np.clip((activity[idx] - mu) / sigma, -3.0, 3.0)

        # Normalize to [0, 1]
        dens = (dens + 3.0) / 6.0
        return dens

    def step(
        self,
        cohort_phases: np.ndarray,
        cohort_activity: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """
        Execute one PLF stabilization step.

        Typically called once per rebalancing cycle (monthly/yearly).

        Args:
            cohort_phases: Phase angles for each cohort
            cohort_activity: Activity/energy for each cohort

        Returns:
            Dictionary containing:
            - phase_map: Smoothed phase coherence
            - fracton_density: Smoothed cluster density
            - damping_mods: Recommended damping multipliers
        """
        phases = cohort_phases.astype(np.float32)
        activity = cohort_activity.astype(np.float32)

        # Compute instantaneous coherence and density
        phase_coh = self._phase_coherence(phases)
        density = self._fracton_density(activity)

        # EMA smoothing to prevent jitter
        self._phase_ema = (
            (1 - self.cfg.phase_smoothing) * self._phase_ema
            + self.cfg.phase_smoothing * phase_coh
        )
        self._density_ema = (
            (1 - self.cfg.density_smoothing) * self._density_ema
            + self.cfg.density_smoothing * density
        )

        # Convert to damping multipliers
        # High coherence/density → increase damping (>1.0)
        # Low coherence/density → decrease damping (<1.0)
        mods = (
            1.0
            + self.cfg.locking_gain * (self._phase_ema - 0.5)
            + self.cfg.cluster_gain * (self._density_ema - 0.5)
        )
        mods = np.clip(mods, self.cfg.min_mod, self.cfg.max_mod)

        return {
            "phase_map": self._phase_ema.copy(),
            "fracton_density": self._density_ema.copy(),
            "damping_mods": mods.astype(np.float32),
        }

    def reset(self):
        """Reset internal EMA state."""
        self._phase_ema = np.zeros(self.grid.size, dtype=np.float32)
        self._density_ema = np.zeros(self.grid.size, dtype=np.float32)


# Example usage and validation
if __name__ == "__main__":
    print("Testing Phase-Locked Fracton Layer (PLF 1.0)...")

    # Create 4x3 torus grid (12 cohorts)
    grid = TorusGrid(width=4, height=3)
    plf = PhaseLockedFractonLayer(grid)

    print(f"\n1. Testing with random phases and activity:")
    phases = np.random.uniform(-np.pi, np.pi, grid.size)
    activity = np.random.rand(grid.size)

    out = plf.step(phases, activity)

    print(f"  Phase map shape: {out['phase_map'].shape}")
    print(f"  Phase map range: [{out['phase_map'].min():.3f}, {out['phase_map'].max():.3f}]")
    print(f"  Density shape: {out['fracton_density'].shape}")
    print(f"  Density range: [{out['fracton_density'].min():.3f}, {out['fracton_density'].max():.3f}]")
    print(f"  Damping mods range: [{out['damping_mods'].min():.3f}, {out['damping_mods'].max():.3f}]")

    # Test high coherence scenario (synchronized phases)
    print(f"\n2. Testing synchronized scenario:")
    sync_phases = np.ones(grid.size) * 0.5  # All cohorts same phase
    sync_activity = np.ones(grid.size) * 0.5

    for i in range(10):
        out = plf.step(sync_phases, sync_activity)

    print(f"  Final phase coherence: {out['phase_map'].mean():.3f}")
    print(f"  Final damping mod: {out['damping_mods'].mean():.3f}")
    print(f"  (Should be > 1.0 to increase damping)")

    # Test diverse scenario (random phases)
    print(f"\n3. Testing diverse scenario:")
    plf.reset()
    diverse_phases = np.random.uniform(-np.pi, np.pi, grid.size)
    diverse_activity = np.random.rand(grid.size)

    for i in range(10):
        out = plf.step(diverse_phases, diverse_activity)

    print(f"  Final phase coherence: {out['phase_map'].mean():.3f}")
    print(f"  Final damping mod: {out['damping_mods'].mean():.3f}")
    print(f"  (Should be ~1.0 or less)")

    print(f"\n✓ PLF 1.0 operational")
