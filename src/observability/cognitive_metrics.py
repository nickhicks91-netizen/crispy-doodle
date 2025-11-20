"""
Cognitive Metrics — OTEL/Prometheus Integration

Telemetry for cognitive protection layers:
- WIL 2.0 gamma tracking
- IBL identity deviation
- DCE desire continuity
- Drift detection
- Erosion risk events
"""

from opentelemetry import trace, metrics
from typing import Optional


# Initialize tracer and meter
tracer = trace.get_tracer("echozero.cognitive")
meter = metrics.get_meter("echozero.cognitive.metrics")


# ============================================================================
# Metric Instruments
# ============================================================================

# WIL 2.0 Metrics
gamma_histogram = meter.create_histogram(
    "wil.gamma.value",
    description="Want parameter (gamma) value",
    unit="1"
)

gamma_drift_histogram = meter.create_histogram(
    "wil.predictive_drift",
    description="Drift between short and long-term gamma trends",
    unit="1"
)

gamma_jump_counter = meter.create_counter(
    "wil.catastrophic_jumps",
    description="Count of catastrophic gamma jumps detected and corrected",
    unit="1"
)

gamma_coherence_guard_counter = meter.create_counter(
    "wil.coherence_guards",
    description="Count of coherence-based gamma restrictions",
    unit="1"
)

# IBL Metrics
identity_deviation_histogram = meter.create_histogram(
    "ibl.identity_deviation",
    description="Deviation from identity core manifold",
    unit="1"
)

identity_erosion_counter = meter.create_counter(
    "ibl.erosion_events",
    description="Count of identity erosion events requiring correction",
    unit="1"
)

identity_core_norm_gauge = meter.create_up_down_counter(
    "ibl.identity_core_norm",
    description="Norm of identity core vector",
    unit="1"
)

# DCE Metrics
desire_shift_histogram = meter.create_histogram(
    "dce.desire_shift",
    description="Magnitude of desire vector shift per tick",
    unit="1"
)

desire_velocity_histogram = meter.create_histogram(
    "dce.desire_velocity",
    description="Velocity (momentum) of desire evolution",
    unit="1"
)

desire_flip_counter = meter.create_counter(
    "dce.adversarial_flips",
    description="Count of adversarial desire flip attempts blocked",
    unit="1"
)


# ============================================================================
# Logging Functions
# ============================================================================

def log_gamma(gamma: float, attributes: Optional[dict] = None):
    """Log gamma value"""
    gamma_histogram.record(float(gamma), attributes=attributes or {})


def log_gamma_drift(drift: float, attributes: Optional[dict] = None):
    """Log predictive drift magnitude"""
    gamma_drift_histogram.record(float(drift), attributes=attributes or {})


def log_gamma_jump(attributes: Optional[dict] = None):
    """Log catastrophic gamma jump event"""
    gamma_jump_counter.add(1, attributes=attributes or {})


def log_coherence_guard(attributes: Optional[dict] = None):
    """Log coherence guard activation"""
    gamma_coherence_guard_counter.add(1, attributes=attributes or {})


def log_identity_deviation(deviation: float, attributes: Optional[dict] = None):
    """Log identity deviation"""
    identity_deviation_histogram.record(float(deviation), attributes=attributes or {})


def log_identity_erosion(attributes: Optional[dict] = None):
    """Log identity erosion event"""
    identity_erosion_counter.add(1, attributes=attributes or {})


def log_identity_core_norm(norm: float, attributes: Optional[dict] = None):
    """Log identity core norm"""
    identity_core_norm_gauge.add(int(norm * 1000), attributes=attributes or {})


def log_desire_shift(shift: float, attributes: Optional[dict] = None):
    """Log desire shift magnitude"""
    desire_shift_histogram.record(float(shift), attributes=attributes or {})


def log_desire_velocity(velocity: float, attributes: Optional[dict] = None):
    """Log desire velocity"""
    desire_velocity_histogram.record(float(velocity), attributes=attributes or {})


def log_desire_flip(attributes: Optional[dict] = None):
    """Log adversarial desire flip blocked"""
    desire_flip_counter.add(1, attributes=attributes or {})


# ============================================================================
# Traced Operations
# ============================================================================

def trace_wil_protection(func):
    """Decorator to trace WIL protection operations"""
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span("wil.protect") as span:
            span.set_attribute("protection.layer", "WIL-2.0")
            result = func(*args, **kwargs)
            return result
    return wrapper


def trace_ibl_boundary(func):
    """Decorator to trace IBL boundary enforcement"""
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span("ibl.enforce_boundary") as span:
            span.set_attribute("protection.layer", "IBL")
            result = func(*args, **kwargs)
            return result
    return wrapper


def trace_dce_stabilization(func):
    """Decorator to trace DCE stabilization"""
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span("dce.stabilize") as span:
            span.set_attribute("protection.layer", "DCE")
            result = func(*args, **kwargs)
            return result
    return wrapper


# ============================================================================
# Batch Logging Utilities
# ============================================================================

class CognitiveMetricsCollector:
    """
    Collects and batches cognitive metrics for efficient telemetry.

    Use this to avoid overwhelming the observability pipeline with
    per-tick metrics when running at high frequencies.
    """

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.gamma_values = []
        self.drift_values = []
        self.identity_deviations = []
        self.desire_shifts = []

    def add_gamma(self, gamma: float):
        """Add gamma value to batch"""
        self.gamma_values.append(gamma)
        if len(self.gamma_values) >= self.batch_size:
            self.flush_gamma()

    def add_drift(self, drift: float):
        """Add drift value to batch"""
        self.drift_values.append(drift)
        if len(self.drift_values) >= self.batch_size:
            self.flush_drift()

    def add_identity_deviation(self, deviation: float):
        """Add identity deviation to batch"""
        self.identity_deviations.append(deviation)
        if len(self.identity_deviations) >= self.batch_size:
            self.flush_identity()

    def add_desire_shift(self, shift: float):
        """Add desire shift to batch"""
        self.desire_shifts.append(shift)
        if len(self.desire_shifts) >= self.batch_size:
            self.flush_desire()

    def flush_gamma(self):
        """Flush gamma batch"""
        if self.gamma_values:
            avg = sum(self.gamma_values) / len(self.gamma_values)
            log_gamma(avg, attributes={"batch_size": len(self.gamma_values)})
            self.gamma_values = []

    def flush_drift(self):
        """Flush drift batch"""
        if self.drift_values:
            avg = sum(self.drift_values) / len(self.drift_values)
            log_gamma_drift(avg, attributes={"batch_size": len(self.drift_values)})
            self.drift_values = []

    def flush_identity(self):
        """Flush identity deviation batch"""
        if self.identity_deviations:
            avg = sum(self.identity_deviations) / len(self.identity_deviations)
            log_identity_deviation(avg, attributes={"batch_size": len(self.identity_deviations)})
            self.identity_deviations = []

    def flush_desire(self):
        """Flush desire shift batch"""
        if self.desire_shifts:
            avg = sum(self.desire_shifts) / len(self.desire_shifts)
            log_desire_shift(avg, attributes={"batch_size": len(self.desire_shifts)})
            self.desire_shifts = []

    def flush_all(self):
        """Flush all batches"""
        self.flush_gamma()
        self.flush_drift()
        self.flush_identity()
        self.flush_desire()


# Example usage
if __name__ == "__main__":
    print("Testing Cognitive Metrics...")

    # Direct logging
    print("\n1. Direct metric logging:")
    log_gamma(0.35, attributes={"component": "test"})
    log_gamma_drift(0.05, attributes={"component": "test"})
    log_identity_deviation(0.08, attributes={"component": "test"})
    log_desire_shift(0.03, attributes={"component": "test"})
    print("  ✓ Direct metrics logged")

    # Event logging
    print("\n2. Event logging:")
    log_gamma_jump(attributes={"severity": "high"})
    log_coherence_guard(attributes={"coherence": 0.10})
    log_identity_erosion(attributes={"deviation": 0.20})
    log_desire_flip(attributes={"magnitude": 2.0})
    print("  ✓ Events logged")

    # Batched collection
    print("\n3. Batched metric collection:")
    collector = CognitiveMetricsCollector(batch_size=10)

    for i in range(25):
        collector.add_gamma(0.35 + i * 0.001)
        collector.add_drift(0.05 + i * 0.0001)
        collector.add_identity_deviation(0.08 + i * 0.0002)
        collector.add_desire_shift(0.03 + i * 0.0001)

    collector.flush_all()
    print("  ✓ Batched metrics flushed")

    print("\n✓ Cognitive metrics tests passed")
