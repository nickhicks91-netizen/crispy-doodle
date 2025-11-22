"""
Metrics Dashboard — Real-time System Monitoring

Aggregates and formats metrics from PLFMetrics for user-facing dashboards.
Provides current state snapshot and health indicators.

DNA Source: OTEL/Prometheus observability → user-friendly transparency
"""

from typing import Dict, Any, List, Optional
import numpy as np
from dataclasses import dataclass, asdict


@dataclass
class HealthStatus:
    """System health indicators."""
    overall_health: str  # "healthy", "warning", "critical"
    sync_risk: float  # 0-1, lower is better
    variance_quality: str  # "excellent", "good", "needs_attention"
    predictive_stability: str  # "stable", "volatile", "unstable"
    mobility_constraint: str  # "enforced", "partial", "unrestricted"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsDashboard:
    """
    Real-time metrics dashboard for CO-HERE-US transparency.

    Aggregates PLF 1.0, PLF 2.0, and Fracton Mode metrics into
    user-friendly formats for visualization.

    Usage:
        dashboard = MetricsDashboard()
        dashboard.update(plf_metrics.get_summary())
        snapshot = dashboard.get_snapshot()
        health = dashboard.get_health()
    """

    def __init__(self):
        """Initialize metrics dashboard."""
        self.current_metrics: Dict[str, float] = {}
        self.health_history: List[HealthStatus] = []
        self.alert_thresholds = {
            "sync_risk": 0.0833,  # 8.33% threshold
            "cohort_variance": 0.012,  # 1.2% threshold
            "curvature_max": 0.5,  # Curvature warning level
            "charge_mean": 0.7,  # High stress level
        }

    def update(self, metrics_summary: Dict[str, float]) -> None:
        """
        Update dashboard with latest metrics.

        Args:
            metrics_summary: Summary dict from PLFMetrics.get_summary()
        """
        self.current_metrics = metrics_summary.copy()

        # Compute and store health status
        health = self._compute_health()
        self.health_history.append(health)

        # Keep last 100 health snapshots
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Get current system snapshot.

        Returns:
            Dict with categorized metrics for display
        """
        m = self.current_metrics

        return {
            "plf1": {
                "phase_coherence": m.get("plf1_phase_mean", 0.0),
                "phase_std": m.get("plf1_phase_std", 0.0),
                "fracton_density": m.get("plf1_density_mean", 0.0),
                "damping_modulation": m.get("plf1_mods_mean", 1.0),
            },
            "plf2": {
                "theta_variance": m.get("plf2_theta_var", 0.0),
                "phi_variance": m.get("plf2_phi_var", 0.0),
                "r_variance": m.get("plf2_r_var", 0.0),
                "curvature_max": m.get("plf2_curvature_max", 0.0),
            },
            "fracton": {
                "charge_mean": m.get("fracton_charge_mean", 0.0),
                "charge_max": m.get("fracton_charge_max", 0.0),
                "movement_restriction": m.get("fracton_movement_mean", 0.0),
                "sync_correlation": abs(m.get("fracton_sync_correlation", 0.0)),
            },
            "orchestrator": {
                "rebalance_fraction": m.get("orch_rebalance_frac", 0.0),
                "cycle_count": int(m.get("orch_cycle", 0)),
            },
        }

    def get_health(self) -> HealthStatus:
        """
        Get current health status.

        Returns:
            HealthStatus object with indicators
        """
        if not self.health_history:
            return HealthStatus(
                overall_health="unknown",
                sync_risk=0.0,
                variance_quality="unknown",
                predictive_stability="unknown",
                mobility_constraint="unknown",
            )

        return self.health_history[-1]

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get active alerts based on thresholds.

        Returns:
            List of alert dicts with severity and message
        """
        alerts = []
        m = self.current_metrics

        # Sync risk alert
        sync_corr = abs(m.get("fracton_sync_correlation", 0.0))
        if sync_corr > self.alert_thresholds["sync_risk"]:
            alerts.append({
                "severity": "warning" if sync_corr < 0.15 else "critical",
                "metric": "sync_risk",
                "value": sync_corr,
                "threshold": self.alert_thresholds["sync_risk"],
                "message": f"Synchronization correlation {sync_corr:.1%} exceeds target {self.alert_thresholds['sync_risk']:.1%}",
            })

        # Cohort variance alert
        theta_var = m.get("plf2_theta_var", 0.0)
        if theta_var > self.alert_thresholds["cohort_variance"]:
            alerts.append({
                "severity": "warning" if theta_var < 0.02 else "critical",
                "metric": "cohort_variance",
                "value": theta_var,
                "threshold": self.alert_thresholds["cohort_variance"],
                "message": f"Cohort variance {theta_var:.1%} exceeds target {self.alert_thresholds['cohort_variance']:.1%}",
            })

        # Curvature alert
        curv_max = m.get("plf2_curvature_max", 0.0)
        if curv_max > self.alert_thresholds["curvature_max"]:
            alerts.append({
                "severity": "warning",
                "metric": "curvature_max",
                "value": curv_max,
                "threshold": self.alert_thresholds["curvature_max"],
                "message": f"Maximum curvature {curv_max:.3f} indicates instability forming",
            })

        # Fracton charge alert
        charge_mean = m.get("fracton_charge_mean", 0.0)
        if charge_mean > self.alert_thresholds["charge_mean"]:
            alerts.append({
                "severity": "warning",
                "metric": "charge_mean",
                "value": charge_mean,
                "threshold": self.alert_thresholds["charge_mean"],
                "message": f"High fracton charge {charge_mean:.3f} indicates widespread stress",
            })

        return alerts

    def _compute_health(self) -> HealthStatus:
        """Compute overall health status from current metrics."""
        m = self.current_metrics

        # Sync risk assessment
        sync_corr = abs(m.get("fracton_sync_correlation", 0.0))

        # Variance quality
        theta_var = m.get("plf2_theta_var", 0.0)
        if theta_var < 0.008:
            variance_quality = "excellent"
        elif theta_var < 0.012:
            variance_quality = "good"
        else:
            variance_quality = "needs_attention"

        # Predictive stability
        curv_max = m.get("plf2_curvature_max", 0.0)
        if curv_max < 0.3:
            predictive_stability = "stable"
        elif curv_max < 0.5:
            predictive_stability = "volatile"
        else:
            predictive_stability = "unstable"

        # Mobility constraint status
        charge_mean = m.get("fracton_charge_mean", 0.0)
        if charge_mean > 0.7:
            mobility_constraint = "enforced"
        elif charge_mean > 0.3:
            mobility_constraint = "partial"
        else:
            mobility_constraint = "unrestricted"

        # Overall health
        alerts = self.get_alerts()
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        warning_alerts = [a for a in alerts if a["severity"] == "warning"]

        if critical_alerts:
            overall_health = "critical"
        elif warning_alerts:
            overall_health = "warning"
        else:
            overall_health = "healthy"

        return HealthStatus(
            overall_health=overall_health,
            sync_risk=sync_corr,
            variance_quality=variance_quality,
            predictive_stability=predictive_stability,
            mobility_constraint=mobility_constraint,
        )


# Example usage
if __name__ == "__main__":
    print("Testing Metrics Dashboard...")

    dashboard = MetricsDashboard()

    # Simulate healthy metrics
    print("\n1. Healthy state:")
    healthy_metrics = {
        "plf1_phase_mean": 0.45,
        "plf1_phase_std": 0.12,
        "plf1_density_mean": 0.52,
        "plf1_mods_mean": 1.02,
        "plf2_theta_var": 0.007,  # Excellent
        "plf2_phi_var": 0.008,
        "plf2_r_var": 0.005,
        "plf2_curvature_max": 0.15,  # Stable
        "fracton_charge_mean": 0.25,  # Unrestricted
        "fracton_charge_max": 0.45,
        "fracton_movement_mean": 0.012,
        "fracton_sync_correlation": 0.03,  # Well below threshold
        "orch_rebalance_frac": 0.25,
        "orch_cycle": 12,
    }

    dashboard.update(healthy_metrics)
    snapshot = dashboard.get_snapshot()
    health = dashboard.get_health()
    alerts = dashboard.get_alerts()

    print(f"  Overall health: {health.overall_health}")
    print(f"  Sync risk: {health.sync_risk:.1%}")
    print(f"  Variance quality: {health.variance_quality}")
    print(f"  Predictive stability: {health.predictive_stability}")
    print(f"  Active alerts: {len(alerts)}")

    # Simulate warning state
    print("\n2. Warning state (high variance):")
    warning_metrics = healthy_metrics.copy()
    warning_metrics["plf2_theta_var"] = 0.015  # Above threshold
    warning_metrics["fracton_sync_correlation"] = 0.10  # Above threshold

    dashboard.update(warning_metrics)
    health = dashboard.get_health()
    alerts = dashboard.get_alerts()

    print(f"  Overall health: {health.overall_health}")
    print(f"  Active alerts: {len(alerts)}")
    for alert in alerts:
        print(f"    - [{alert['severity'].upper()}] {alert['message']}")

    # Simulate critical state
    print("\n3. Critical state (high curvature + sync):")
    critical_metrics = healthy_metrics.copy()
    critical_metrics["plf2_curvature_max"] = 0.65  # Unstable
    critical_metrics["fracton_sync_correlation"] = 0.18  # Critical
    critical_metrics["fracton_charge_mean"] = 0.85  # High stress

    dashboard.update(critical_metrics)
    health = dashboard.get_health()
    alerts = dashboard.get_alerts()

    print(f"  Overall health: {health.overall_health}")
    print(f"  Predictive stability: {health.predictive_stability}")
    print(f"  Active alerts: {len(alerts)}")
    for alert in alerts:
        print(f"    - [{alert['severity'].upper()}] {alert['message']}")

    print("\n✓ Metrics Dashboard operational")
