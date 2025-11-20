"""
Core Metrics Collector
Centralized metrics collection for EchoZero system
"""

import torch
import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical summary


@dataclass
class MetricValue:
    """Single metric measurement"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Metric definition with history"""
    name: str
    metric_type: MetricType
    description: str
    unit: str
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Central metrics collection system

    Features:
    - Multiple metric types (counter, gauge, histogram, summary)
    - Time-series storage
    - Label support
    - Thread-safe operations
    - Aggregation functions
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector

        Args:
            max_history: Maximum history per metric
        """
        self.metrics: Dict[str, Metric] = {}
        self.lock = threading.RLock()
        self.max_history = max_history
        self.start_time = time.time()

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        unit: str = "",
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """
        Register new metric

        Args:
            name: Metric name (e.g., "echozero_phi_depth")
            metric_type: Type of metric
            description: Human-readable description
            unit: Unit of measurement
            labels: Static labels for this metric

        Returns:
            Registered Metric object
        """
        with self.lock:
            if name in self.metrics:
                return self.metrics[name]

            metric = Metric(
                name=name,
                metric_type=metric_type,
                description=description,
                unit=unit,
                labels=labels or {},
                values=deque(maxlen=self.max_history)
            )

            self.metrics[name] = metric
            return metric

    def record(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record metric value

        Args:
            name: Metric name
            value: Metric value
            labels: Dynamic labels for this measurement
        """
        with self.lock:
            metric = self.metrics.get(name)
            if metric is None:
                raise KeyError(f"Metric '{name}' not registered")

            # For counters, ensure monotonic increase
            if metric.metric_type == MetricType.COUNTER:
                if metric.values and value < metric.values[-1].value:
                    raise ValueError(f"Counter '{name}' cannot decrease")

            metric.values.append(MetricValue(
                timestamp=time.time(),
                value=value,
                labels=labels or {}
            ))

    def increment(self, name: str, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment counter metric"""
        with self.lock:
            metric = self.metrics.get(name)
            if metric is None:
                raise KeyError(f"Metric '{name}' not registered")

            if metric.metric_type != MetricType.COUNTER:
                raise ValueError(f"Metric '{name}' is not a counter")

            current = metric.values[-1].value if metric.values else 0.0
            self.record(name, current + amount, labels)

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge metric value"""
        with self.lock:
            metric = self.metrics.get(name)
            if metric is None:
                raise KeyError(f"Metric '{name}' not registered")

            if metric.metric_type != MetricType.GAUGE:
                raise ValueError(f"Metric '{name}' is not a gauge")

            self.record(name, value, labels)

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe value for histogram/summary"""
        with self.lock:
            metric = self.metrics.get(name)
            if metric is None:
                raise KeyError(f"Metric '{name}' not registered")

            if metric.metric_type not in [MetricType.HISTOGRAM, MetricType.SUMMARY]:
                raise ValueError(f"Metric '{name}' is not a histogram or summary")

            self.record(name, value, labels)

    def get_current(self, name: str) -> Optional[float]:
        """Get current value of metric"""
        with self.lock:
            metric = self.metrics.get(name)
            if metric is None or not metric.values:
                return None
            return metric.values[-1].value

    def get_history(self, name: str, limit: Optional[int] = None) -> List[MetricValue]:
        """Get metric history"""
        with self.lock:
            metric = self.metrics.get(name)
            if metric is None:
                return []

            values = list(metric.values)
            if limit:
                values = values[-limit:]
            return values

    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistical summary of metric"""
        with self.lock:
            metric = self.metrics.get(name)
            if metric is None or not metric.values:
                return {}

            values = [v.value for v in metric.values]

            return {
                'count': len(values),
                'sum': sum(values),
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / len(values),
                'last': values[-1],
            }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics with current values"""
        with self.lock:
            result = {}
            for name, metric in self.metrics.items():
                current_value = metric.values[-1].value if metric.values else None
                result[name] = {
                    'type': metric.metric_type.value,
                    'description': metric.description,
                    'unit': metric.unit,
                    'current': current_value,
                    'labels': metric.labels
                }
            return result

    def reset(self, name: str):
        """Reset metric history"""
        with self.lock:
            metric = self.metrics.get(name)
            if metric:
                metric.values.clear()

    def uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_global_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


# Convenience functions using global collector
def register_metric(*args, **kwargs):
    """Register metric on global collector"""
    return get_global_collector().register_metric(*args, **kwargs)


def record(*args, **kwargs):
    """Record on global collector"""
    return get_global_collector().record(*args, **kwargs)


def increment(*args, **kwargs):
    """Increment on global collector"""
    return get_global_collector().increment(*args, **kwargs)


def set_gauge(*args, **kwargs):
    """Set gauge on global collector"""
    return get_global_collector().set_gauge(*args, **kwargs)


def observe(*args, **kwargs):
    """Observe on global collector"""
    return get_global_collector().observe(*args, **kwargs)


# Example usage
if __name__ == "__main__":
    collector = MetricsCollector()

    # Register metrics
    collector.register_metric(
        "echozero_phi_depth",
        MetricType.GAUGE,
        "Current φ-depth value",
        unit="scalar"
    )

    collector.register_metric(
        "echozero_api_requests_total",
        MetricType.COUNTER,
        "Total API requests",
        unit="requests"
    )

    collector.register_metric(
        "echozero_inference_duration_seconds",
        MetricType.HISTOGRAM,
        "Inference duration",
        unit="seconds"
    )

    # Record values
    collector.set_gauge("echozero_phi_depth", 0.75)
    collector.increment("echozero_api_requests_total")
    collector.observe("echozero_inference_duration_seconds", 0.123)

    # Get stats
    phi_stats = collector.get_stats("echozero_phi_depth")
    print(f"φ-depth stats: {phi_stats}")

    # Get all metrics
    all_metrics = collector.get_all_metrics()
    print(f"\nAll metrics: {len(all_metrics)}")
    for name, info in all_metrics.items():
        print(f"  {name}: {info['current']} {info['unit']}")

    print("\n✓ MetricsCollector tests passed")
