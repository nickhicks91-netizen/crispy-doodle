"""
Drift Curves — Historical Phase/Curvature/Charge Tracking

Maintains time-series data for visualizing system evolution over time.
Enables trend analysis and forecasting validation.

DNA Source: EchoZero temporal coherence tracking → financial drift monitoring
"""

from typing import Dict, List, Any, Optional
import numpy as np
from collections import deque
from dataclasses import dataclass, field


@dataclass
class DriftSnapshot:
    """Single point in time for drift tracking."""
    cycle: int
    timestamp: float
    phase_mean: float
    phase_std: float
    curvature_max: float
    curvature_mean: float
    charge_mean: float
    charge_max: float
    sync_correlation: float
    theta_variance: float
    phi_variance: float
    r_variance: float


class DriftCurveTracker:
    """
    Historical drift curve tracking for transparency.

    Maintains time-series of key stability metrics to visualize
    system evolution and validate predictive performance.

    Usage:
        tracker = DriftCurveTracker(max_history=1000)
        tracker.record(cycle=1, metrics=plf_metrics.get_summary())
        curves = tracker.get_curves(last_n=100)
        trend = tracker.get_trend("curvature_max", window=20)
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize drift curve tracker.

        Args:
            max_history: Maximum snapshots to retain
        """
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)

    def record(
        self,
        cycle: int,
        metrics: Dict[str, float],
        timestamp: Optional[float] = None
    ) -> None:
        """
        Record a drift snapshot.

        Args:
            cycle: Current cycle/year number
            metrics: Metrics dict from PLFMetrics.get_summary()
            timestamp: Unix timestamp (defaults to current time)
        """
        import time
        if timestamp is None:
            timestamp = time.time()

        snapshot = DriftSnapshot(
            cycle=cycle,
            timestamp=timestamp,
            phase_mean=metrics.get("plf1_phase_mean", 0.0),
            phase_std=metrics.get("plf1_phase_std", 0.0),
            curvature_max=metrics.get("plf2_curvature_max", 0.0),
            curvature_mean=metrics.get("plf2_curvature_mean", 0.0),
            charge_mean=metrics.get("fracton_charge_mean", 0.0),
            charge_max=metrics.get("fracton_charge_max", 0.0),
            sync_correlation=abs(metrics.get("fracton_sync_correlation", 0.0)),
            theta_variance=metrics.get("plf2_theta_var", 0.0),
            phi_variance=metrics.get("plf2_phi_var", 0.0),
            r_variance=metrics.get("plf2_r_var", 0.0),
        )

        self.history.append(snapshot)

    def get_curves(self, last_n: Optional[int] = None) -> Dict[str, List[float]]:
        """
        Get time-series curves for visualization.

        Args:
            last_n: Return only last N snapshots (None = all)

        Returns:
            Dict mapping metric names to time-series arrays
        """
        if not self.history:
            return {}

        snapshots = list(self.history)
        if last_n is not None:
            snapshots = snapshots[-last_n:]

        curves = {
            "cycles": [s.cycle for s in snapshots],
            "timestamps": [s.timestamp for s in snapshots],
            "phase_mean": [s.phase_mean for s in snapshots],
            "phase_std": [s.phase_std for s in snapshots],
            "curvature_max": [s.curvature_max for s in snapshots],
            "curvature_mean": [s.curvature_mean for s in snapshots],
            "charge_mean": [s.charge_mean for s in snapshots],
            "charge_max": [s.charge_max for s in snapshots],
            "sync_correlation": [s.sync_correlation for s in snapshots],
            "theta_variance": [s.theta_variance for s in snapshots],
            "phi_variance": [s.phi_variance for s in snapshots],
            "r_variance": [s.r_variance for s in snapshots],
        }

        return curves

    def get_trend(
        self,
        metric: str,
        window: int = 10,
        last_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get trend analysis for a specific metric.

        Args:
            metric: Metric name (e.g., "curvature_max")
            window: Rolling average window size
            last_n: Analyze only last N snapshots

        Returns:
            Dict with trend data (values, rolling_avg, direction, rate)
        """
        curves = self.get_curves(last_n=last_n)

        if metric not in curves or len(curves[metric]) < 2:
            return {
                "values": [],
                "rolling_avg": [],
                "direction": "unknown",
                "rate": 0.0,
            }

        values = np.array(curves[metric])

        # Compute rolling average
        if len(values) >= window:
            rolling_avg = np.convolve(
                values,
                np.ones(window) / window,
                mode='valid'
            )
        else:
            rolling_avg = values

        # Trend direction (linear regression on recent data)
        recent_window = min(20, len(values))
        recent_values = values[-recent_window:]
        x = np.arange(recent_window)

        if len(recent_values) > 1:
            slope, _ = np.polyfit(x, recent_values, 1)
            if abs(slope) < 0.001:
                direction = "stable"
            elif slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
        else:
            slope = 0.0
            direction = "unknown"

        return {
            "values": values.tolist(),
            "rolling_avg": rolling_avg.tolist(),
            "direction": direction,
            "rate": float(slope),
        }

    def get_volatility(self, metric: str, window: int = 20) -> float:
        """
        Get recent volatility for a metric.

        Args:
            metric: Metric name
            window: Window size for std calculation

        Returns:
            Standard deviation over window
        """
        curves = self.get_curves(last_n=window)

        if metric not in curves or len(curves[metric]) < 2:
            return 0.0

        return float(np.std(curves[metric]))

    def detect_anomalies(
        self,
        metric: str,
        threshold: float = 3.0,
        last_n: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous values using Z-score.

        Args:
            metric: Metric name
            threshold: Z-score threshold for anomaly
            last_n: Look back N snapshots

        Returns:
            List of anomaly dicts with cycle, value, z_score
        """
        curves = self.get_curves(last_n=last_n)

        if metric not in curves or len(curves[metric]) < 10:
            return []

        values = np.array(curves[metric])
        cycles = curves["cycles"]

        mean = np.mean(values)
        std = np.std(values)

        if std < 1e-9:
            return []

        z_scores = (values - mean) / std

        anomalies = []
        for i, (cycle, val, z) in enumerate(zip(cycles, values, z_scores)):
            if abs(z) > threshold:
                anomalies.append({
                    "cycle": cycle,
                    "value": float(val),
                    "z_score": float(z),
                    "deviation": "high" if z > 0 else "low",
                })

        return anomalies


# Example usage
if __name__ == "__main__":
    import time
    print("Testing Drift Curve Tracker...")

    tracker = DriftCurveTracker(max_history=100)

    # Simulate 50 cycles of data
    print("\n1. Recording 50 cycles of simulated data:")
    np.random.seed(42)

    base_curvature = 0.2
    for cycle in range(50):
        # Simulate drift with occasional spikes
        noise = np.random.randn() * 0.05
        spike = 0.3 if cycle in [15, 32] else 0.0  # Anomalies

        metrics = {
            "plf1_phase_mean": 0.5 + np.random.randn() * 0.05,
            "plf1_phase_std": 0.15 + np.random.randn() * 0.02,
            "plf2_curvature_max": base_curvature + noise + spike,
            "plf2_curvature_mean": base_curvature * 0.6 + noise,
            "fracton_charge_mean": 0.4 + np.random.randn() * 0.1,
            "fracton_charge_max": 0.6 + np.random.randn() * 0.1,
            "fracton_sync_correlation": 0.05 + abs(np.random.randn() * 0.02),
            "plf2_theta_var": 0.008 + abs(np.random.randn() * 0.002),
            "plf2_phi_var": 0.007 + abs(np.random.randn() * 0.002),
            "plf2_r_var": 0.006 + abs(np.random.randn() * 0.002),
        }

        tracker.record(cycle=cycle, metrics=metrics)
        time.sleep(0.001)  # Simulate time progression

    print(f"  Recorded {len(tracker.history)} snapshots")

    # Get trend analysis
    print("\n2. Curvature trend analysis:")
    trend = tracker.get_trend("curvature_max", window=5, last_n=50)
    print(f"  Direction: {trend['direction']}")
    print(f"  Rate: {trend['rate']:.6f}")
    print(f"  Current value: {trend['values'][-1]:.6f}")
    print(f"  Rolling avg (latest): {trend['rolling_avg'][-1]:.6f}")

    # Detect anomalies
    print("\n3. Anomaly detection:")
    anomalies = tracker.detect_anomalies("curvature_max", threshold=2.5, last_n=50)
    print(f"  Found {len(anomalies)} anomalies")
    for anom in anomalies:
        print(f"    - Cycle {anom['cycle']}: {anom['value']:.6f} (z={anom['z_score']:.2f}, {anom['deviation']})")

    # Volatility measurement
    print("\n4. Recent volatility:")
    vol = tracker.get_volatility("curvature_max", window=20)
    print(f"  Curvature volatility: {vol:.6f}")

    # Get curves for plotting
    print("\n5. Retrieve curves for visualization:")
    curves = tracker.get_curves(last_n=10)
    print(f"  Available metrics: {[k for k in curves.keys() if k not in ['cycles', 'timestamps']]}")
    print(f"  Latest 10 curvature_max values: {[f'{v:.3f}' for v in curves['curvature_max']]}")

    print("\n✓ Drift Curve Tracker operational")
