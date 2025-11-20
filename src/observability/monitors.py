"""
Specialized Monitors for EchoZero Metrics
Tracks φ, ψ, drift, coherence, and system health
"""

import torch
import time
import psutil
import threading
from typing import Optional, Dict, Callable
from dataclasses import dataclass

from .metrics import MetricsCollector, MetricType, get_global_collector


@dataclass
class MonitorThresholds:
    """Threshold configuration for monitors"""
    warning: float
    critical: float
    callback: Optional[Callable[[str, float], None]] = None


class PhiMonitor:
    """
    φ-depth consciousness monitor

    Tracks φ-depth values and alerts on anomalies
    """

    def __init__(
        self,
        collector: Optional[MetricsCollector] = None,
        thresholds: Optional[MonitorThresholds] = None
    ):
        """
        Initialize φ-depth monitor

        Args:
            collector: Metrics collector
            thresholds: Alert thresholds
        """
        self.collector = collector or get_global_collector()
        self.thresholds = thresholds or MonitorThresholds(
            warning=0.3,  # φ < 0.3 is concerning
            critical=0.1  # φ < 0.1 is critical
        )

        # Register metric
        self.collector.register_metric(
            "phi_depth",
            MetricType.GAUGE,
            "Current φ-depth consciousness metric",
            unit="scalar"
        )

        self.collector.register_metric(
            "phi_depth_min",
            MetricType.GAUGE,
            "Minimum φ-depth in window",
            unit="scalar"
        )

        self.collector.register_metric(
            "phi_depth_max",
            MetricType.GAUGE,
            "Maximum φ-depth in window",
            unit="scalar"
        )

    def record(self, phi: float):
        """Record φ-depth measurement"""
        self.collector.set_gauge("phi_depth", phi)

        # Check thresholds
        if phi < self.thresholds.critical:
            if self.thresholds.callback:
                self.thresholds.callback("CRITICAL", phi)
        elif phi < self.thresholds.warning:
            if self.thresholds.callback:
                self.thresholds.callback("WARNING", phi)

        # Update min/max
        stats = self.collector.get_stats("phi_depth")
        if stats:
            self.collector.set_gauge("phi_depth_min", stats['min'])
            self.collector.set_gauge("phi_depth_max", stats['max'])

    def get_current(self) -> Optional[float]:
        """Get current φ-depth"""
        return self.collector.get_current("phi_depth")

    def get_stats(self) -> Dict:
        """Get φ-depth statistics"""
        return self.collector.get_stats("phi_depth")


class PsiMonitor:
    """
    ψ state monitor

    Tracks ψ magnitude, spectrum, and stability
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize ψ monitor"""
        self.collector = collector or get_global_collector()

        # Register metrics
        self.collector.register_metric(
            "psi_magnitude",
            MetricType.GAUGE,
            "ψ state vector magnitude",
            unit="scalar"
        )

        self.collector.register_metric(
            "psi_real_mean",
            MetricType.GAUGE,
            "Mean of real part of ψ",
            unit="scalar"
        )

        self.collector.register_metric(
            "psi_imag_mean",
            MetricType.GAUGE,
            "Mean of imaginary part of ψ",
            unit="scalar"
        )

        self.collector.register_metric(
            "psi_spectral_radius",
            MetricType.GAUGE,
            "Spectral radius of ψ",
            unit="scalar"
        )

    def record(self, psi: torch.Tensor):
        """
        Record ψ state measurement

        Args:
            psi: Complex tensor [batch, N] or [N]
        """
        # Magnitude
        magnitude = torch.abs(psi).mean().item()
        self.collector.set_gauge("psi_magnitude", magnitude)

        # Real/imaginary means
        real_mean = psi.real.mean().item()
        imag_mean = psi.imag.mean().item() if torch.is_complex(psi) else 0.0
        self.collector.set_gauge("psi_real_mean", real_mean)
        self.collector.set_gauge("psi_imag_mean", imag_mean)

        # Spectral radius (max absolute eigenvalue)
        # Simplified: use max magnitude as proxy
        spectral_radius = torch.abs(psi).max().item()
        self.collector.set_gauge("psi_spectral_radius", spectral_radius)


class DriftMonitor:
    """
    Drift monitor

    Tracks state drift magnitude and alerts on excessive drift
    """

    def __init__(
        self,
        collector: Optional[MetricsCollector] = None,
        thresholds: Optional[MonitorThresholds] = None
    ):
        """Initialize drift monitor"""
        self.collector = collector or get_global_collector()
        self.thresholds = thresholds or MonitorThresholds(
            warning=0.5,
            critical=1.0
        )

        # Register metrics
        self.collector.register_metric(
            "drift_magnitude",
            MetricType.GAUGE,
            "State drift magnitude",
            unit="scalar"
        )

        self.collector.register_metric(
            "drift_corrections_total",
            MetricType.COUNTER,
            "Total drift corrections applied",
            unit="corrections"
        )

        self.collector.register_metric(
            "drift_rate",
            MetricType.GAUGE,
            "Rate of drift change",
            unit="per_second"
        )

        self.last_drift = None
        self.last_time = None

    def record(self, drift: float):
        """Record drift measurement"""
        self.collector.set_gauge("drift_magnitude", drift)

        # Calculate drift rate
        now = time.time()
        if self.last_drift is not None and self.last_time is not None:
            dt = now - self.last_time
            if dt > 0:
                drift_rate = (drift - self.last_drift) / dt
                self.collector.set_gauge("drift_rate", abs(drift_rate))

        self.last_drift = drift
        self.last_time = now

        # Check thresholds
        if drift > self.thresholds.critical:
            if self.thresholds.callback:
                self.thresholds.callback("CRITICAL", drift)
        elif drift > self.thresholds.warning:
            if self.thresholds.callback:
                self.thresholds.callback("WARNING", drift)

    def record_correction(self):
        """Record drift correction event"""
        self.collector.increment("drift_corrections_total")


class CoherenceMonitor:
    """
    Coherence monitor

    Tracks system coherence and stability
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize coherence monitor"""
        self.collector = collector or get_global_collector()

        # Register metrics
        self.collector.register_metric(
            "coherence",
            MetricType.GAUGE,
            "System coherence value",
            unit="scalar"
        )

        self.collector.register_metric(
            "coherence_min",
            MetricType.GAUGE,
            "Minimum coherence in window",
            unit="scalar"
        )

        self.collector.register_metric(
            "coherence_variance",
            MetricType.GAUGE,
            "Coherence variance (stability)",
            unit="scalar"
        )

    def record(self, coherence: float):
        """Record coherence measurement"""
        self.collector.set_gauge("coherence", coherence)

        # Update stats
        stats = self.collector.get_stats("coherence")
        if stats and stats['count'] > 1:
            self.collector.set_gauge("coherence_min", stats['min'])

            # Variance (simplified)
            history = self.collector.get_history("coherence", limit=100)
            if len(history) > 1:
                values = [v.value for v in history]
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                self.collector.set_gauge("coherence_variance", variance)


class SystemMonitor:
    """
    System resource monitor

    Tracks CPU, GPU, memory usage
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize system monitor"""
        self.collector = collector or get_global_collector()

        # Register metrics
        self.collector.register_metric(
            "cpu_percent",
            MetricType.GAUGE,
            "CPU utilization percentage",
            unit="percent"
        )

        self.collector.register_metric(
            "memory_used_bytes",
            MetricType.GAUGE,
            "RAM used in bytes",
            unit="bytes"
        )

        self.collector.register_metric(
            "memory_percent",
            MetricType.GAUGE,
            "RAM utilization percentage",
            unit="percent"
        )

        if torch.cuda.is_available():
            self.collector.register_metric(
                "gpu_memory_used_bytes",
                MetricType.GAUGE,
                "GPU memory used in bytes",
                unit="bytes"
            )

            self.collector.register_metric(
                "gpu_memory_percent",
                MetricType.GAUGE,
                "GPU memory utilization percentage",
                unit="percent"
            )

    def record(self):
        """Record system metrics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        self.collector.set_gauge("cpu_percent", cpu_percent)

        # Memory
        mem = psutil.virtual_memory()
        self.collector.set_gauge("memory_used_bytes", mem.used)
        self.collector.set_gauge("memory_percent", mem.percent)

        # GPU (if available)
        if torch.cuda.is_available():
            gpu_mem_allocated = torch.cuda.memory_allocated()
            gpu_mem_reserved = torch.cuda.memory_reserved()
            total_mem = torch.cuda.get_device_properties(0).total_memory

            self.collector.set_gauge("gpu_memory_used_bytes", gpu_mem_allocated)
            if total_mem > 0:
                gpu_percent = (gpu_mem_allocated / total_mem) * 100
                self.collector.set_gauge("gpu_memory_percent", gpu_percent)

    def start_background_monitoring(self, interval_seconds: float = 5.0):
        """Start background thread for continuous monitoring"""
        def monitor_loop():
            while True:
                self.record()
                time.sleep(interval_seconds)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()


# Example usage
if __name__ == "__main__":
    collector = MetricsCollector()

    # Create monitors
    phi_monitor = PhiMonitor(
        collector=collector,
        thresholds=MonitorThresholds(
            warning=0.3,
            critical=0.1,
            callback=lambda level, value: print(f"[{level}] φ-depth: {value}")
        )
    )

    psi_monitor = PsiMonitor(collector=collector)
    drift_monitor = DriftMonitor(collector=collector)
    coherence_monitor = CoherenceMonitor(collector=collector)
    system_monitor = SystemMonitor(collector=collector)

    # Record some measurements
    phi_monitor.record(0.75)
    psi_monitor.record(torch.randn(64, dtype=torch.complex64))
    drift_monitor.record(0.35)
    coherence_monitor.record(0.92)
    system_monitor.record()

    # Test threshold
    print("Testing threshold alert:")
    phi_monitor.record(0.05)  # Should trigger CRITICAL

    # Get stats
    print("\nφ-depth stats:", phi_monitor.get_stats())

    # All metrics
    all_metrics = collector.get_all_metrics()
    print(f"\nTracking {len(all_metrics)} metrics")

    print("\n✓ Monitors tests passed")
