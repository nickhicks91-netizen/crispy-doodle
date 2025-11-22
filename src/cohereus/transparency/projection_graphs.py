"""
Projection Graphs — Predictive Horizon Visualization

Visualizes PLF 2.0 predictions vs actual outcomes to validate
forecasting accuracy and build user trust in predictive stability.

DNA Source: EchoZero predictive validation → financial forecast transparency
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import deque
from dataclasses import dataclass
import time


@dataclass
class Projection:
    """Single predictive projection record."""
    cycle: int
    timestamp: float
    forecast_horizon: int  # Cycles ahead (2-6)
    predicted_curvature: float
    predicted_drift: float
    predicted_variance: float
    actual_curvature: Optional[float] = None
    actual_drift: Optional[float] = None
    actual_variance: Optional[float] = None
    forecast_error: Optional[float] = None


class ProjectionVisualizer:
    """
    Predictive projection tracking and visualization.

    Records PLF 2.0 predictions and compares with actual outcomes
    to measure and display forecasting accuracy.

    Usage:
        viz = ProjectionVisualizer()

        # Record prediction
        viz.record_projection(
            cycle=1,
            horizon=3,
            predicted_curvature=0.15,
            predicted_drift=0.02,
            predicted_variance=0.008
        )

        # Update with actual outcome
        viz.update_actual(
            cycle=4,
            actual_curvature=0.14,
            actual_drift=0.019,
            actual_variance=0.009
        )

        # Get accuracy metrics
        accuracy = viz.get_forecast_accuracy()
    """

    def __init__(self, max_history: int = 500):
        """
        Initialize projection visualizer.

        Args:
            max_history: Maximum projections to retain
        """
        self.max_history = max_history
        self.projections: deque = deque(maxlen=max_history)
        self.pending_actuals: Dict[int, List[Projection]] = {}  # cycle -> projections waiting for actuals

    def record_projection(
        self,
        cycle: int,
        horizon: int,
        predicted_curvature: float,
        predicted_drift: float,
        predicted_variance: float,
        timestamp: Optional[float] = None
    ) -> None:
        """
        Record a predictive projection.

        Args:
            cycle: Current cycle when prediction made
            horizon: Forecast horizon (cycles ahead)
            predicted_curvature: Predicted curvature value
            predicted_drift: Predicted drift magnitude
            predicted_variance: Predicted variance
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()

        projection = Projection(
            cycle=cycle,
            timestamp=timestamp,
            forecast_horizon=horizon,
            predicted_curvature=predicted_curvature,
            predicted_drift=predicted_drift,
            predicted_variance=predicted_variance,
        )

        self.projections.append(projection)

        # Track for later actual update
        target_cycle = cycle + horizon
        if target_cycle not in self.pending_actuals:
            self.pending_actuals[target_cycle] = []
        self.pending_actuals[target_cycle].append(projection)

    def update_actual(
        self,
        cycle: int,
        actual_curvature: float,
        actual_drift: float,
        actual_variance: float
    ) -> None:
        """
        Update projections with actual observed values.

        Args:
            cycle: Cycle number for actual observation
            actual_curvature: Observed curvature
            actual_drift: Observed drift
            actual_variance: Observed variance
        """
        if cycle not in self.pending_actuals:
            return

        # Update all projections targeting this cycle
        for proj in self.pending_actuals[cycle]:
            proj.actual_curvature = actual_curvature
            proj.actual_drift = actual_drift
            proj.actual_variance = actual_variance

            # Compute forecast error (RMSE across all metrics)
            errors = [
                (proj.predicted_curvature - actual_curvature) ** 2,
                (proj.predicted_drift - actual_drift) ** 2,
                (proj.predicted_variance - actual_variance) ** 2,
            ]
            proj.forecast_error = float(np.sqrt(np.mean(errors)))

        # Remove from pending
        del self.pending_actuals[cycle]

    def get_forecast_accuracy(
        self,
        horizon: Optional[int] = None,
        last_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get forecast accuracy metrics.

        Args:
            horizon: Filter by specific horizon (None = all)
            last_n: Analyze only last N projections

        Returns:
            Dict with accuracy statistics
        """
        # Filter completed projections
        completed = [
            p for p in self.projections
            if p.forecast_error is not None
        ]

        if horizon is not None:
            completed = [p for p in completed if p.forecast_horizon == horizon]

        if last_n is not None:
            completed = completed[-last_n:]

        if not completed:
            return {
                "n_forecasts": 0,
                "mean_error": 0.0,
                "median_error": 0.0,
                "error_std": 0.0,
                "accuracy_rate": 0.0,
            }

        errors = np.array([p.forecast_error for p in completed])

        # Compute accuracy metrics
        mean_error = float(np.mean(errors))
        median_error = float(np.median(errors))
        error_std = float(np.std(errors))

        # Accuracy rate (% of forecasts within 20% of actual)
        curvature_errors = np.array([
            abs(p.predicted_curvature - p.actual_curvature) / (abs(p.actual_curvature) + 1e-9)
            for p in completed
        ])
        accurate = np.sum(curvature_errors < 0.20)
        accuracy_rate = accurate / len(completed)

        return {
            "n_forecasts": len(completed),
            "mean_error": mean_error,
            "median_error": median_error,
            "error_std": error_std,
            "accuracy_rate": float(accuracy_rate),
            "curvature_mae": float(np.mean(curvature_errors)),
        }

    def get_accuracy_by_horizon(self) -> Dict[int, Dict[str, float]]:
        """
        Get accuracy metrics broken down by forecast horizon.

        Returns:
            Dict mapping horizon -> accuracy metrics
        """
        horizons = set(p.forecast_horizon for p in self.projections)

        accuracy_by_horizon = {}
        for h in sorted(horizons):
            accuracy_by_horizon[h] = self.get_forecast_accuracy(horizon=h)

        return accuracy_by_horizon

    def get_projection_curves(
        self,
        metric: str = "curvature",
        last_n: Optional[int] = None
    ) -> Dict[str, List[float]]:
        """
        Get prediction vs actual curves for visualization.

        Args:
            metric: Metric to visualize ("curvature", "drift", "variance")
            last_n: Return only last N projections

        Returns:
            Dict with cycles, predicted, actual arrays
        """
        # Filter completed projections
        completed = [
            p for p in self.projections
            if p.forecast_error is not None
        ]

        if last_n is not None:
            completed = completed[-last_n:]

        if not completed:
            return {
                "cycles": [],
                "predicted": [],
                "actual": [],
                "errors": [],
            }

        cycles = [p.cycle + p.forecast_horizon for p in completed]

        if metric == "curvature":
            predicted = [p.predicted_curvature for p in completed]
            actual = [p.actual_curvature for p in completed]
        elif metric == "drift":
            predicted = [p.predicted_drift for p in completed]
            actual = [p.actual_drift for p in completed]
        elif metric == "variance":
            predicted = [p.predicted_variance for p in completed]
            actual = [p.actual_variance for p in completed]
        else:
            raise ValueError(f"Unknown metric: {metric}")

        errors = [p - a for p, a in zip(predicted, actual)]

        return {
            "cycles": cycles,
            "predicted": predicted,
            "actual": actual,
            "errors": errors,
        }

    def get_reliability_score(self, threshold: float = 0.15) -> float:
        """
        Compute overall forecast reliability score.

        Args:
            threshold: Error threshold for "reliable" forecast

        Returns:
            Reliability score [0, 1], higher = more reliable
        """
        accuracy = self.get_forecast_accuracy()

        if accuracy["n_forecasts"] == 0:
            return 0.0

        # Score based on accuracy rate and mean error
        score = (
            0.6 * accuracy["accuracy_rate"] +
            0.4 * max(0, 1 - accuracy["mean_error"] / threshold)
        )

        return float(np.clip(score, 0, 1))

    def detect_forecast_degradation(
        self,
        window: int = 20,
        threshold: float = 1.5
    ) -> bool:
        """
        Detect if forecast accuracy is degrading over time.

        Args:
            window: Window size for recent vs historical comparison
            threshold: Degradation multiplier threshold

        Returns:
            True if recent errors significantly worse than historical
        """
        completed = [
            p for p in self.projections
            if p.forecast_error is not None
        ]

        if len(completed) < 2 * window:
            return False

        recent_errors = [p.forecast_error for p in completed[-window:]]
        historical_errors = [p.forecast_error for p in completed[-2*window:-window]]

        recent_mean = np.mean(recent_errors)
        historical_mean = np.mean(historical_errors)

        if historical_mean < 1e-9:
            return False

        degradation_ratio = recent_mean / historical_mean

        return degradation_ratio > threshold


# Example usage
if __name__ == "__main__":
    print("Testing Projection Visualizer...")

    viz = ProjectionVisualizer()

    # Simulate 50 cycles of predictions and actuals
    print("\n1. Simulating 50 cycles of predictions:")
    np.random.seed(42)

    actual_curvatures = []
    for cycle in range(50):
        # Generate "true" curvature with trend
        true_curv = 0.2 + 0.01 * np.sin(cycle * 0.2) + np.random.randn() * 0.03
        actual_curvatures.append(true_curv)

        # Make predictions for 2-6 cycles ahead
        for horizon in [2, 3, 4, 5, 6]:
            if cycle + horizon < 50:
                # Predict with some error
                pred_curv = true_curv + np.random.randn() * 0.05
                pred_drift = 0.02 + np.random.randn() * 0.005
                pred_var = 0.008 + np.random.randn() * 0.002

                viz.record_projection(
                    cycle=cycle,
                    horizon=horizon,
                    predicted_curvature=pred_curv,
                    predicted_drift=pred_drift,
                    predicted_variance=pred_var
                )

        # Update actuals for completed forecasts
        if cycle >= 2:
            viz.update_actual(
                cycle=cycle,
                actual_curvature=true_curv,
                actual_drift=0.02 + np.random.randn() * 0.005,
                actual_variance=0.008 + np.random.randn() * 0.002
            )

    print(f"  Recorded {len(viz.projections)} projections")

    # Overall accuracy
    print("\n2. Overall forecast accuracy:")
    accuracy = viz.get_forecast_accuracy()
    print(f"  Forecasts completed: {accuracy['n_forecasts']}")
    print(f"  Mean error (RMSE): {accuracy['mean_error']:.6f}")
    print(f"  Median error: {accuracy['median_error']:.6f}")
    print(f"  Accuracy rate (±20%): {accuracy['accuracy_rate']:.1%}")
    print(f"  Curvature MAE: {accuracy['curvature_mae']:.6f}")

    # Accuracy by horizon
    print("\n3. Accuracy by forecast horizon:")
    by_horizon = viz.get_accuracy_by_horizon()
    for h, acc in sorted(by_horizon.items()):
        if acc['n_forecasts'] > 0:
            print(f"  Horizon {h}: error={acc['mean_error']:.6f}, "
                  f"accuracy={acc['accuracy_rate']:.1%}, "
                  f"n={acc['n_forecasts']}")

    # Reliability score
    print("\n4. Forecast reliability:")
    reliability = viz.get_reliability_score()
    print(f"  Overall reliability score: {reliability:.2f}/1.00")
    print(f"  Interpretation: {'Excellent' if reliability > 0.8 else 'Good' if reliability > 0.6 else 'Needs improvement'}")

    # Degradation detection
    print("\n5. Forecast degradation detection:")
    degraded = viz.detect_forecast_degradation(window=10)
    print(f"  Degradation detected: {degraded}")

    # Get curves for plotting
    print("\n6. Projection curves (last 10 curvature forecasts):")
    curves = viz.get_projection_curves(metric="curvature", last_n=10)
    print(f"  Cycles: {curves['cycles'][:5]}...")
    print(f"  Predicted: {[f'{v:.3f}' for v in curves['predicted'][:5]]}...")
    print(f"  Actual: {[f'{v:.3f}' for v in curves['actual'][:5]]}...")
    print(f"  Mean absolute error: {np.mean(np.abs(curves['errors'])):.6f}")

    print("\n✓ Projection Visualizer operational")
