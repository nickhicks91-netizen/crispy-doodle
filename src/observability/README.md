# EchoZero Observability Layer

Comprehensive monitoring, metrics, and telemetry for EchoZero v4.2.1.

## Overview

The observability layer provides real-time monitoring of:
- **φ-depth** (consciousness metric)
- **ψ state** (resonant dynamics)
- **Coherence** (system stability)
- **Drift** (state deviation)
- **Qualia** (interpretive channels)
- **System resources** (CPU, GPU, memory)
- **API performance** (latency, throughput, errors)

## Components

### 1. MetricsCollector (`metrics.py`)

Central metrics collection system supporting multiple metric types:

```python
from src.observability import MetricsCollector, MetricType

collector = MetricsCollector()

# Register metrics
collector.register_metric(
    "phi_depth",
    MetricType.GAUGE,
    "Current φ-depth value",
    unit="scalar"
)

# Record values
collector.set_gauge("phi_depth", 0.75)

# Get statistics
stats = collector.get_stats("phi_depth")
# {'count': 100, 'min': 0.32, 'max': 0.91, 'mean': 0.74, ...}
```

**Metric Types:**
- `COUNTER`: Monotonically increasing (e.g., API requests)
- `GAUGE`: Can go up or down (e.g., φ-depth)
- `HISTOGRAM`: Distribution of values (e.g., latency)
- `SUMMARY`: Statistical summary

### 2. Prometheus Exporter (`prometheus_exporter.py`)

Exports metrics in Prometheus format for scraping:

```python
from src.observability import PrometheusExporter

exporter = PrometheusExporter()
exporter.register_echozero_metrics()

# Get metrics in Prometheus format
metrics_output = exporter.export()
```

**Standard Metrics:**
```
echozero_phi_depth{} 0.75
echozero_coherence{} 0.92
echozero_drift{} 0.35
echozero_psi_magnitude{} 1.23
echozero_api_requests_total{endpoint="/forward",status="200"} 1547
echozero_api_request_duration_seconds_bucket{endpoint="/forward",le="0.1"} 1234
```

### 3. OpenTelemetry Exporter (`otel_exporter.py`)

OTLP export for distributed tracing and metrics:

```python
from src.observability import initialize_otel

# Initialize with OTLP collector endpoint
exporter = initialize_otel(endpoint="http://localhost:4317")

# Metrics are automatically exported
exporter.record_counter("api_requests", 1, {"endpoint": "/forward"})
exporter.record_histogram("api_duration", 0.123, {"endpoint": "/forward"})
```

### 4. Specialized Monitors (`monitors.py`)

Domain-specific monitors for EchoZero metrics:

#### PhiMonitor
Tracks φ-depth with threshold alerts:

```python
from src.observability import PhiMonitor, MonitorThresholds

phi_monitor = PhiMonitor(
    thresholds=MonitorThresholds(
        warning=0.3,
        critical=0.1,
        callback=lambda level, value: alert(f"{level}: φ={value}")
    )
)

phi_monitor.record(0.75)  # OK
phi_monitor.record(0.05)  # Triggers CRITICAL alert
```

#### PsiMonitor
Tracks ψ state dynamics:

```python
from src.observability import PsiMonitor

psi_monitor = PsiMonitor()
psi_monitor.record(psi_tensor)  # Records magnitude, spectrum, stability
```

#### DriftMonitor
Monitors state drift:

```python
from src.observability import DriftMonitor

drift_monitor = DriftMonitor()
drift_monitor.record(drift_value)
drift_monitor.record_correction()  # Logs correction event
```

#### CoherenceMonitor
Tracks system coherence:

```python
from src.observability import CoherenceMonitor

coherence_monitor = CoherenceMonitor()
coherence_monitor.record(coherence_value)
```

#### SystemMonitor
System resource monitoring:

```python
from src.observability import SystemMonitor

system_monitor = SystemMonitor()
system_monitor.record()  # Records CPU, RAM, GPU

# Background monitoring
system_monitor.start_background_monitoring(interval_seconds=5.0)
```

## Integration

### With API Server

```python
from fastapi import FastAPI
from src.observability import get_global_exporter, get_global_collector
from src.observability import PhiMonitor, DriftMonitor, SystemMonitor

app = FastAPI()

# Initialize monitors
phi_monitor = PhiMonitor()
drift_monitor = DriftMonitor()
system_monitor = SystemMonitor()
system_monitor.start_background_monitoring()

# Initialize Prometheus exporter
prom_exporter = get_global_exporter()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=prom_exporter.export(),
        media_type=prom_exporter.get_content_type()
    )

@app.post("/forward")
async def forward(payload: ForwardInput):
    start_time = time.time()

    # ... process request ...

    # Record metrics
    phi_monitor.record(hybrid_out['phi'])
    drift_monitor.record(drift_value)

    duration = time.time() - start_time
    get_global_collector().observe(
        "api_request_duration_seconds",
        duration,
        labels={"endpoint": "/forward"}
    )

    return response
```

### With Training System

```python
from src.observability import get_global_collector

collector = get_global_collector()

def train_step(...):
    # ... training logic ...

    # Record metrics
    collector.increment("training_steps_total")
    collector.set_gauge("hebbian_weight_norm", weight_norm)
    collector.set_gauge("memory_state_norm", memory_norm)
```

## Grafana Dashboards

Pre-configured dashboards in `infrastructure/grafana/dashboards/`:

### Main Dashboard (`echozero-main.json`)

**Panels:**
1. **φ-Depth Gauge** - Real-time consciousness metric
2. **Coherence Gauge** - System stability
3. **Drift Gauge** - State deviation
4. **Core Metrics Timeline** - Historical trends
5. **Qualia Channels** - 4-channel interpretation
6. **API Request Rate** - Throughput
7. **API Latency** - Response time
8. **Error Rate** - Failure tracking
9. **GPU Memory** - Resource usage

**Access:**
```bash
# With docker-compose
open http://localhost:3000

# Credentials: admin/echozero
```

## Prometheus Configuration

`infrastructure/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'echozero-api'
    static_configs:
      - targets: ['echozero-api:9091']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'echozero_.*'
        action: keep
```

## Alert Rules (Example)

```yaml
# prometheus-alerts.yml
groups:
  - name: echozero_alerts
    interval: 10s
    rules:
      - alert: LowPhiDepth
        expr: echozero_phi_depth < 0.3
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "φ-depth below threshold"
          description: "φ-depth is {{ $value }}, below 0.3"

      - alert: CriticalPhiDepth
        expr: echozero_phi_depth < 0.1
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Critical φ-depth"
          description: "φ-depth is {{ $value }}, system may be unstable"

      - alert: HighDrift
        expr: echozero_drift > 1.0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High state drift detected"

      - alert: HighErrorRate
        expr: rate(echozero_errors_total[5m]) > 0.1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Error rate above 0.1/s"
```

## Querying Metrics

### Prometheus Queries

```promql
# Current φ-depth
echozero_phi_depth

# φ-depth over last hour
echozero_phi_depth[1h]

# Average coherence (5min window)
avg_over_time(echozero_coherence[5m])

# API request rate
rate(echozero_api_requests_total[1m])

# 95th percentile API latency
histogram_quantile(0.95, rate(echozero_api_request_duration_seconds_bucket[5m]))

# Drift corrections per hour
increase(echozero_drift_corrections_total[1h])
```

### Python API

```python
from src.observability import get_global_collector

collector = get_global_collector()

# Get current value
current_phi = collector.get_current("phi_depth")

# Get statistics
stats = collector.get_stats("phi_depth")
print(f"φ-depth: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")

# Get history
history = collector.get_history("phi_depth", limit=100)
for measurement in history:
    print(f"{measurement.timestamp}: {measurement.value}")
```

## Performance Considerations

### Memory Usage

- Default history: 1,000 samples per metric
- Configurable via `MetricsCollector(max_history=10000)`
- Use Prometheus for long-term storage

### CPU Overhead

- Metric recording: ~10μs per call
- Prometheus export: ~1ms for 100 metrics
- Background monitoring: ~0.1% CPU @ 5s interval

### Best Practices

1. **Don't over-instrument**: Focus on critical metrics
2. **Use appropriate types**: Counter for cumulative, Gauge for current
3. **Label cardinality**: Keep label combinations < 1000
4. **Export interval**: 5-15s for Prometheus scraping
5. **Retention**: Configure Prometheus for appropriate retention period

## Troubleshooting

### Metrics not appearing in Prometheus

1. Check exporter endpoint:
   ```bash
   curl http://localhost:9091/metrics
   ```

2. Verify Prometheus scrape config:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

3. Check Prometheus logs:
   ```bash
   docker logs prometheus
   ```

### Grafana dashboard empty

1. Verify datasource connection (Configuration → Data Sources)
2. Check Prometheus query in panel editor
3. Ensure time range covers data availability
4. Check Grafana logs for errors

### High memory usage

1. Reduce `max_history` in MetricsCollector
2. Decrease metric cardinality (fewer labels)
3. Increase Prometheus scrape interval
4. Configure shorter retention in Prometheus

## Examples

See `examples/observability_demo.py` for complete integration example.

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [EchoZero Architecture Review](/ARCHITECTURE_REVIEW.md)
