"""
PLF & Fracton Mode Metrics — OTEL Integration

Observability for PLF 2.0 and Fracton Mode:
- Phase coherence and curvature metrics
- Fracton charge and mobility metrics
- Stability scores
- Torus topology metrics

DNA Source: EchoZero cognitive_metrics.py patterns
"""

from typing import Dict, Any, Optional
import numpy as np


class PLFMetrics:
    """
    Lightweight metrics collector for PLF + Torus + Fracton.

    Tracks:
    - Phase map statistics
    - Fracton density
    - Damping modulation
    - Curvature signals
    - Fracton charge
    - Mobility restrictions
    - Stability scores
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.history = []

    def record_plf1(self, plf_output: Dict[str, Any]) -> Dict[str, float]:
        """
        Record PLF 1.0 metrics.

        Args:
            plf_output: Output from PLF 1.0 step()

        Returns:
            Dictionary of metrics
        """
        phase = plf_output["phase_map"]
        dens = plf_output["fracton_density"]
        mods = plf_output["damping_mods"]

        metrics = {
            "plf1_phase_mean": float(np.mean(phase)),
            "plf1_phase_std": float(np.std(phase)),
            "plf1_density_mean": float(np.mean(dens)),
            "plf1_density_std": float(np.std(dens)),
            "plf1_mods_mean": float(np.mean(mods)),
            "plf1_mods_std": float(np.std(mods)),
            "plf1_mods_min": float(np.min(mods)),
            "plf1_mods_max": float(np.max(mods)),
        }

        return metrics

    def record_plf2(self, state: Dict[str, np.ndarray], curvature: np.ndarray) -> Dict[str, float]:
        """
        Record PLF 2.0 metrics.

        Args:
            state: PLF 2.0 stabilized state
            curvature: Curvature vector

        Returns:
            Dictionary of metrics
        """
        metrics = {
            "plf2_theta_mean": float(np.mean(state["theta"])),
            "plf2_theta_std": float(np.std(state["theta"])),
            "plf2_phi_mean": float(np.mean(state["phi"])),
            "plf2_phi_std": float(np.std(state["phi"])),
            "plf2_r_mean": float(np.mean(state["r"])),
            "plf2_r_std": float(np.std(state["r"])),
            "plf2_curvature_mean": float(np.mean(curvature)),
            "plf2_curvature_max": float(np.max(np.abs(curvature))),
        }

        return metrics

    def record_fracton(
        self,
        charge: np.ndarray,
        restricted_state: Dict[str, np.ndarray],
        original_state: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """
        Record Fracton Mode metrics.

        Args:
            charge: Fracton charge array
            restricted_state: State after fracton constraints
            original_state: State before constraints

        Returns:
            Dictionary of metrics
        """
        # Measure movement restriction
        theta_movement = np.mean(np.abs(restricted_state["theta"] - original_state["theta"]))

        # Measure synchronization (correlation)
        sync = np.corrcoef(restricted_state["theta"], restricted_state["r"])[0, 1]

        metrics = {
            "fracton_charge_mean": float(np.mean(charge)),
            "fracton_charge_max": float(np.max(charge)),
            "fracton_theta_movement": float(theta_movement),
            "fracton_sync_correlation": float(abs(sync)),
            "fracton_theta_variance": float(np.var(restricted_state["theta"])),
            "fracton_mobility_restriction": float(1.0 - theta_movement),
        }

        return metrics

    def record_tick(self, tick_out: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record complete orchestrator tick metrics.

        Args:
            tick_out: Output from TorusCohortOrchestrator.tick()

        Returns:
            Aggregated metrics
        """
        plf = tick_out.get("plf", {})

        # Base metrics
        metrics = {
            "cycle": tick_out.get("cycle", 0),
            "rebalance_count": len(tick_out.get("rebalance_ids", [])),
            "rebalance_fraction": float(len(tick_out.get("rebalance_ids", [])) / 12.0),
        }

        # Add PLF 1.0 metrics if available
        if plf:
            metrics.update(self.record_plf1(plf))

        self.history.append(metrics)
        return metrics

    def get_summary(self, last_n: int = 10) -> Dict[str, float]:
        """
        Get summary statistics over last N cycles.

        Args:
            last_n: Number of recent cycles to summarize

        Returns:
            Summary statistics
        """
        if not self.history:
            return {}

        recent = self.history[-last_n:]

        summary = {
            "avg_rebalance_fraction": float(np.mean([m["rebalance_fraction"] for m in recent])),
            "avg_phase_coherence": float(np.mean([m.get("plf1_phase_mean", 0) for m in recent])),
            "avg_damping_mod": float(np.mean([m.get("plf1_mods_mean", 1.0) for m in recent])),
            "total_cycles": len(self.history),
        }

        return summary


# Example usage
if __name__ == "__main__":
    print("Testing PLF Metrics...")

    metrics = PLFMetrics()

    # Simulate PLF 1.0 output
    print("\n1. Recording PLF 1.0 metrics:")
    plf1_output = {
        "phase_map": np.random.rand(12) * 0.5,
        "fracton_density": np.random.rand(12) * 0.8,
        "damping_mods": 1.0 + np.random.randn(12) * 0.1,
    }

    plf1_metrics = metrics.record_plf1(plf1_output)
    print(f"  Phase mean: {plf1_metrics['plf1_phase_mean']:.4f}")
    print(f"  Damping mod mean: {plf1_metrics['plf1_mods_mean']:.4f}")

    # Simulate PLF 2.0 output
    print("\n2. Recording PLF 2.0 metrics:")
    state = {
        "theta": np.random.randn(12) * 0.3,
        "phi": np.random.randn(12) * 0.2,
        "r": 0.5 + np.random.rand(12) * 0.3,
    }
    curvature = np.random.randn(12) * 0.5

    plf2_metrics = metrics.record_plf2(state, curvature)
    print(f"  Theta std: {plf2_metrics['plf2_theta_std']:.4f}")
    print(f"  Curvature max: {plf2_metrics['plf2_curvature_max']:.4f}")

    # Simulate Fracton Mode output
    print("\n3. Recording Fracton Mode metrics:")
    charge = np.random.rand(12) * 0.8
    original_state = {
        "theta": np.random.randn(12),
        "phi": np.random.randn(12),
        "r": 0.5 + np.random.rand(12),
    }
    restricted_state = {
        "theta": original_state["theta"] * 0.9,  # Restricted movement
        "phi": original_state["phi"] * 0.9,
        "r": original_state["r"] * 0.95,
    }

    fracton_metrics = metrics.record_fracton(charge, restricted_state, original_state)
    print(f"  Charge mean: {fracton_metrics['fracton_charge_mean']:.4f}")
    print(f"  Mobility restriction: {fracton_metrics['fracton_mobility_restriction']:.4f}")
    print(f"  Sync correlation: {fracton_metrics['fracton_sync_correlation']:.4f}")

    # Record multiple ticks
    print("\n4. Recording orchestrator ticks:")
    for i in range(10):
        tick_out = {
            "cycle": i + 1,
            "rebalance_ids": list(range(i % 3 + 1)),
            "plf": plf1_output,
        }
        tick_metrics = metrics.record_tick(tick_out)

        if i % 3 == 0:
            print(f"  Cycle {tick_metrics['cycle']}: "
                  f"{tick_metrics['rebalance_fraction']:.2%} rebalancing")

    # Get summary
    print("\n5. Summary statistics:")
    summary = metrics.get_summary(last_n=10)
    for key, value in summary.items():
        print(f"  {key}: {value:.4f}")

    print("\n✓ PLF Metrics operational")
