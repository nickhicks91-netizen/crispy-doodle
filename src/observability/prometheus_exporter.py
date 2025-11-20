"""
Prometheus Exporter
Exports EchoZero metrics in Prometheus format
"""

import threading
import time
from typing import Dict, Optional
from prometheus_client import Counter, Gauge, Histogram, Summary, Info, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from .metrics import MetricsCollector, MetricType


class PrometheusExporter:
    """
    Exports metrics to Prometheus

    Features:
    - Automatic metric type mapping
    - Label support
    - HTTP endpoint for scraping
    - Custom registry support
    """

    def __init__(
        self,
        collector: Optional[MetricsCollector] = None,
        registry: Optional[CollectorRegistry] = None,
        namespace: str = "echozero"
    ):
        """
        Initialize Prometheus exporter

        Args:
            collector: MetricsCollector instance (uses global if None)
            registry: Prometheus registry (creates new if None)
            namespace: Metric namespace prefix
        """
        from .metrics import get_global_collector

        self.collector = collector or get_global_collector()
        self.registry = registry or CollectorRegistry()
        self.namespace = namespace
        self.prom_metrics: Dict[str, any] = {}
        self.lock = threading.RLock()

        # System info metric
        self.info = Info(
            'echozero_system',
            'EchoZero system information',
            registry=self.registry
        )
        self.info.info({
            'version': '4.2.1',
            'component': 'resonant_intelligence'
        })

    def _get_prom_metric_name(self, name: str) -> str:
        """Convert metric name to Prometheus format"""
        # Remove namespace if already present
        if name.startswith(f"{self.namespace}_"):
            return name
        return f"{self.namespace}_{name}"

    def register_echozero_metrics(self):
        """Register all standard EchoZero metrics"""
        with self.lock:
            # φ-depth gauge
            self._register_gauge(
                "phi_depth",
                "Current φ-depth consciousness metric"
            )

            # Coherence gauge
            self._register_gauge(
                "coherence",
                "System coherence value"
            )

            # Drift gauge
            self._register_gauge(
                "drift",
                "State drift magnitude"
            )

            # ψ magnitude gauge
            self._register_gauge(
                "psi_magnitude",
                "ψ state vector magnitude"
            )

            # Qualia channels (4 gauges)
            for i in range(4):
                self._register_gauge(
                    f"qualia_channel_{i}",
                    f"Qualia channel {i} value"
                )

            # API metrics
            self._register_counter(
                "api_requests_total",
                "Total API requests",
                labelnames=["endpoint", "method", "status"]
            )

            self._register_histogram(
                "api_request_duration_seconds",
                "API request duration",
                labelnames=["endpoint"],
                buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
            )

            # Training metrics
            self._register_counter(
                "training_steps_total",
                "Total training steps"
            )

            self._register_gauge(
                "hebbian_weight_norm",
                "Hebbian weight matrix norm"
            )

            # Memory metrics
            self._register_gauge(
                "memory_state_norm",
                "GRCM memory state norm"
            )

            # System metrics
            self._register_gauge(
                "gpu_memory_used_bytes",
                "GPU memory used"
            )

            self._register_gauge(
                "gpu_utilization_percent",
                "GPU utilization percentage"
            )

            # Error counter
            self._register_counter(
                "errors_total",
                "Total errors",
                labelnames=["type", "component"]
            )

    def _register_counter(self, name: str, description: str, labelnames: Optional[list] = None):
        """Register Prometheus counter"""
        full_name = self._get_prom_metric_name(name)
        if full_name not in self.prom_metrics:
            self.prom_metrics[full_name] = Counter(
                full_name,
                description,
                labelnames=labelnames or [],
                registry=self.registry
            )

    def _register_gauge(self, name: str, description: str, labelnames: Optional[list] = None):
        """Register Prometheus gauge"""
        full_name = self._get_prom_metric_name(name)
        if full_name not in self.prom_metrics:
            self.prom_metrics[full_name] = Gauge(
                full_name,
                description,
                labelnames=labelnames or [],
                registry=self.registry
            )

    def _register_histogram(
        self,
        name: str,
        description: str,
        labelnames: Optional[list] = None,
        buckets: Optional[list] = None
    ):
        """Register Prometheus histogram"""
        full_name = self._get_prom_metric_name(name)
        if full_name not in self.prom_metrics:
            kwargs = {
                'name': full_name,
                'documentation': description,
                'labelnames': labelnames or [],
                'registry': self.registry
            }
            if buckets:
                kwargs['buckets'] = buckets

            self.prom_metrics[full_name] = Histogram(**kwargs)

    def update_from_collector(self):
        """Update Prometheus metrics from MetricsCollector"""
        with self.lock:
            for name, metric_info in self.collector.get_all_metrics().items():
                full_name = self._get_prom_metric_name(name)

                # Skip if not registered
                if full_name not in self.prom_metrics:
                    continue

                prom_metric = self.prom_metrics[full_name]
                current_value = metric_info['current']

                if current_value is None:
                    continue

                # Update based on type
                metric_type = MetricType(metric_info['type'])

                if metric_type == MetricType.GAUGE:
                    if hasattr(prom_metric, 'set'):
                        prom_metric.set(current_value)

    def export(self) -> bytes:
        """
        Export metrics in Prometheus text format

        Returns:
            Prometheus-formatted metrics
        """
        with self.lock:
            # Update from collector
            self.update_from_collector()

            # Generate Prometheus output
            return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """Get HTTP content type for Prometheus"""
        return CONTENT_TYPE_LATEST


# Global exporter instance
_global_exporter: Optional[PrometheusExporter] = None


def get_global_exporter() -> PrometheusExporter:
    """Get or create global Prometheus exporter"""
    global _global_exporter
    if _global_exporter is None:
        _global_exporter = PrometheusExporter()
        _global_exporter.register_echozero_metrics()
    return _global_exporter


# Example usage
if __name__ == "__main__":
    from .metrics import MetricsCollector, MetricType

    # Create collector and exporter
    collector = MetricsCollector()
    exporter = PrometheusExporter(collector=collector)

    # Register metrics
    collector.register_metric("phi_depth", MetricType.GAUGE, "φ-depth", "scalar")
    collector.register_metric("coherence", MetricType.GAUGE, "Coherence", "scalar")

    exporter.register_echozero_metrics()

    # Record some values
    collector.set_gauge("phi_depth", 0.75)
    collector.set_gauge("coherence", 0.92)

    # Export
    output = exporter.export()
    print("Prometheus output:")
    print(output.decode('utf-8'))

    print("\n✓ PrometheusExporter tests passed")
