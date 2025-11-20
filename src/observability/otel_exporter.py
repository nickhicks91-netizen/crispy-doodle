"""
OpenTelemetry Exporter
Exports metrics and traces using OpenTelemetry
"""

import time
from typing import Optional, Dict
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

from .metrics import MetricsCollector, MetricType


class OTELExporter:
    """
    OpenTelemetry exporter for EchoZero metrics

    Features:
    - OTLP gRPC export
    - Automatic metric type mapping
    - Resource attributes
    - Periodic export
    """

    def __init__(
        self,
        collector: Optional[MetricsCollector] = None,
        endpoint: str = "http://localhost:4317",
        service_name: str = "echozero",
        export_interval_ms: int = 10000
    ):
        """
        Initialize OTEL exporter

        Args:
            collector: MetricsCollector instance
            endpoint: OTLP endpoint
            service_name: Service name for resource
            export_interval_ms: Export interval in milliseconds
        """
        from .metrics import get_global_collector

        self.collector = collector or get_global_collector()

        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "4.2.1",
            "service.instance.id": f"{service_name}-{int(time.time())}"
        })

        # Create OTLP exporter
        otlp_exporter = OTLPMetricExporter(
            endpoint=endpoint,
            insecure=True  # Use TLS in production
        )

        # Create metric reader with periodic export
        reader = PeriodicExportingMetricReader(
            otlp_exporter,
            export_interval_millis=export_interval_ms
        )

        # Create meter provider
        provider = MeterProvider(
            resource=resource,
            metric_readers=[reader]
        )

        # Set global meter provider
        metrics.set_meter_provider(provider)

        # Get meter
        self.meter = metrics.get_meter(service_name)

        # OTEL instruments
        self.instruments: Dict[str, any] = {}

    def register_echozero_metrics(self):
        """Register EchoZero metrics as OTEL instruments"""
        # φ-depth
        self.instruments['phi_depth'] = self.meter.create_gauge(
            name="echozero.phi_depth",
            description="Current φ-depth consciousness metric",
            unit="scalar"
        )

        # Coherence
        self.instruments['coherence'] = self.meter.create_gauge(
            name="echozero.coherence",
            description="System coherence value",
            unit="scalar"
        )

        # Drift
        self.instruments['drift'] = self.meter.create_gauge(
            name="echozero.drift",
            description="State drift magnitude",
            unit="scalar"
        )

        # ψ magnitude
        self.instruments['psi_magnitude'] = self.meter.create_gauge(
            name="echozero.psi_magnitude",
            description="ψ state vector magnitude",
            unit="scalar"
        )

        # API requests counter
        self.instruments['api_requests'] = self.meter.create_counter(
            name="echozero.api_requests.total",
            description="Total API requests",
            unit="requests"
        )

        # API duration histogram
        self.instruments['api_duration'] = self.meter.create_histogram(
            name="echozero.api_request.duration",
            description="API request duration",
            unit="seconds"
        )

        # Training steps
        self.instruments['training_steps'] = self.meter.create_counter(
            name="echozero.training_steps.total",
            description="Total training steps",
            unit="steps"
        )

        # Errors
        self.instruments['errors'] = self.meter.create_counter(
            name="echozero.errors.total",
            description="Total errors",
            unit="errors"
        )

    def update_gauge(self, name: str, value: float, attributes: Optional[Dict] = None):
        """Update gauge instrument"""
        if name in self.instruments:
            # OTEL gauges use callbacks - store value for callback
            # In production, use observable gauges with callbacks
            pass

    def record_counter(self, name: str, value: float = 1.0, attributes: Optional[Dict] = None):
        """Record counter increment"""
        if name in self.instruments:
            self.instruments[name].add(value, attributes or {})

    def record_histogram(self, name: str, value: float, attributes: Optional[Dict] = None):
        """Record histogram observation"""
        if name in self.instruments:
            self.instruments[name].record(value, attributes or {})


# Global OTEL exporter
_global_otel_exporter: Optional[OTELExporter] = None


def get_global_otel_exporter() -> Optional[OTELExporter]:
    """Get global OTEL exporter (may be None if not initialized)"""
    return _global_otel_exporter


def initialize_otel(endpoint: str = "http://localhost:4317") -> OTELExporter:
    """Initialize global OTEL exporter"""
    global _global_otel_exporter
    _global_otel_exporter = OTELExporter(endpoint=endpoint)
    _global_otel_exporter.register_echozero_metrics()
    return _global_otel_exporter


# Example usage
if __name__ == "__main__":
    print("OTEL Exporter - requires OTLP collector running")
    print("Example initialization:")
    print("  exporter = initialize_otel('http://localhost:4317')")
    print("  exporter.record_counter('api_requests', 1, {'endpoint': '/forward'})")
    print("\n✓ OTELExporter module loaded")
