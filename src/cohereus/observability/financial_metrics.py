"""
CO-HERE-US Financial Metrics — OTEL Integration

Observability for national-scale financial system:
- Risk metrics (RHL)
- Strategy metrics (SIL)
- Position metrics (PSE)
- Liquidity metrics (IDS)
- Portfolio performance

DNA Source: src/observability/cognitive_metrics.py (EchoZero v4.2.1)
"""

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter
)
from typing import Dict, Any, Optional


# Initialize OTEL meter
meter_provider = MeterProvider(
    metric_readers=[
        PeriodicExportingMetricReader(
            ConsoleMetricExporter(),
            export_interval_millis=60000  # Export every 60 seconds
        )
    ]
)
metrics.set_meter_provider(meter_provider)

meter = metrics.get_meter("cohereus.financial", version="1.0.0")


# =============================================================================
# Risk Harmonization Layer (RHL) Metrics
# =============================================================================

risk_allocation_histogram = meter.create_histogram(
    name="rhl.risk_allocation",
    description="Current risk allocation percentage",
    unit="percent"
)

risk_drift_histogram = meter.create_histogram(
    name="rhl.risk_drift",
    description="Risk drift magnitude between timescales",
    unit="1"
)

risk_volatility_guard_counter = meter.create_counter(
    name="rhl.volatility_guard_activations",
    description="Number of times volatility guard was activated",
    unit="1"
)

risk_drawdown_detector_counter = meter.create_counter(
    name="rhl.drawdown_detector_activations",
    description="Number of times drawdown detector was activated",
    unit="1"
)


def log_risk_allocation(risk: float, attributes: Optional[Dict[str, Any]] = None):
    """Log risk allocation metric"""
    risk_allocation_histogram.record(risk * 100.0, attributes=attributes or {})


def log_risk_drift(drift: float, attributes: Optional[Dict[str, Any]] = None):
    """Log risk drift metric"""
    risk_drift_histogram.record(drift, attributes=attributes or {})


# =============================================================================
# Strategy Identity Layer (SIL) Metrics
# =============================================================================

strategy_deviation_histogram = meter.create_histogram(
    name="sil.strategy_deviation",
    description="Deviation from strategy core",
    unit="1"
)

strategy_erosion_counter = meter.create_counter(
    name="sil.erosion_events",
    description="Number of times strategy erosion threshold was exceeded",
    unit="1"
)

strategy_core_norm_gauge = meter.create_observable_gauge(
    name="sil.core_norm",
    description="Strategy core norm (magnitude)",
    unit="1"
)


def log_strategy_deviation(deviation: float, attributes: Optional[Dict[str, Any]] = None):
    """Log strategy deviation metric"""
    strategy_deviation_histogram.record(deviation, attributes=attributes or {})


# =============================================================================
# Position Smoothing Engine (PSE) Metrics
# =============================================================================

position_velocity_histogram = meter.create_histogram(
    name="pse.position_velocity",
    description="Position change velocity (rate of change)",
    unit="1/day"
)

position_shift_histogram = meter.create_histogram(
    name="pse.position_shift",
    description="Magnitude of position shifts",
    unit="1"
)

position_flip_counter = meter.create_counter(
    name="pse.flip_events",
    description="Number of position flip attempts",
    unit="1"
)


def log_position_velocity(velocity: float, attributes: Optional[Dict[str, Any]] = None):
    """Log position velocity metric"""
    position_velocity_histogram.record(velocity, attributes=attributes or {})


def log_position_shift(shift: float, attributes: Optional[Dict[str, Any]] = None):
    """Log position shift metric"""
    position_shift_histogram.record(shift, attributes=attributes or {})


# =============================================================================
# Inter-Bot Diversity System (IDS) Metrics
# =============================================================================

diversity_score_gauge = meter.create_observable_gauge(
    name="ids.diversity_score",
    description="Phase diversity score (0=synchronized, 1=diverse)",
    unit="1"
)

synchronization_risk_counter = meter.create_counter(
    name="ids.synchronization_risk_events",
    description="Number of synchronization risk events detected",
    unit="1"
)

liquidity_pressure_histogram = meter.create_histogram(
    name="ids.liquidity_pressure",
    description="Liquidity pressure ratio (rebalancing volume / market volume)",
    unit="1"
)


def log_synchronization_risk(sync_fraction: float, attributes: Optional[Dict[str, Any]] = None):
    """Log synchronization risk event"""
    synchronization_risk_counter.add(1, attributes=attributes or {})


def log_liquidity_pressure(pressure_ratio: float, attributes: Optional[Dict[str, Any]] = None):
    """Log liquidity pressure metric"""
    liquidity_pressure_histogram.record(pressure_ratio, attributes=attributes or {})


# =============================================================================
# Portfolio Performance Metrics
# =============================================================================

portfolio_return_histogram = meter.create_histogram(
    name="portfolio.daily_return",
    description="Daily portfolio return",
    unit="percent"
)

portfolio_volatility_histogram = meter.create_histogram(
    name="portfolio.volatility",
    description="Portfolio volatility (standard deviation)",
    unit="percent"
)

portfolio_sharpe_ratio_gauge = meter.create_observable_gauge(
    name="portfolio.sharpe_ratio",
    description="Sharpe ratio (risk-adjusted return)",
    unit="1"
)

total_aum_gauge = meter.create_observable_gauge(
    name="portfolio.total_aum",
    description="Total assets under management",
    unit="USD"
)


def log_portfolio_return(returns: float, attributes: Optional[Dict[str, Any]] = None):
    """Log portfolio return metric"""
    portfolio_return_histogram.record(returns * 100.0, attributes=attributes or {})


def log_portfolio_volatility(volatility: float, attributes: Optional[Dict[str, Any]] = None):
    """Log portfolio volatility metric"""
    portfolio_volatility_histogram.record(volatility * 100.0, attributes=attributes or {})


def log_total_aum(aum: float, attributes: Optional[Dict[str, Any]] = None):
    """Log total AUM (placeholder for observable gauge)"""
    # Observable gauges require callback functions
    pass


# =============================================================================
# Account Metrics
# =============================================================================

account_balance_histogram = meter.create_histogram(
    name="account.balance",
    description="Individual account balance",
    unit="USD"
)

cohort_size_gauge = meter.create_observable_gauge(
    name="cohort.size",
    description="Number of accounts in cohort",
    unit="accounts"
)


def log_account_balance(balance: float, attributes: Optional[Dict[str, Any]] = None):
    """Log account balance metric"""
    account_balance_histogram.record(balance, attributes=attributes or {})


# =============================================================================
# Batched Metrics Collector (for high-frequency systems)
# =============================================================================

class FinancialMetricsCollector:
    """
    Batched metrics collector for high-frequency financial systems

    DNA Source: CognitiveMetricsCollector (EchoZero)
    """

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.risk_allocations = []
        self.strategy_deviations = []
        self.position_velocities = []
        self.portfolio_returns = []

    def add_risk_allocation(self, risk: float):
        """Add risk allocation to batch"""
        self.risk_allocations.append(risk)
        if len(self.risk_allocations) >= self.batch_size:
            self.flush_risk()

    def add_strategy_deviation(self, deviation: float):
        """Add strategy deviation to batch"""
        self.strategy_deviations.append(deviation)
        if len(self.strategy_deviations) >= self.batch_size:
            self.flush_strategy()

    def add_position_velocity(self, velocity: float):
        """Add position velocity to batch"""
        self.position_velocities.append(velocity)
        if len(self.position_velocities) >= self.batch_size:
            self.flush_position()

    def add_portfolio_return(self, returns: float):
        """Add portfolio return to batch"""
        self.portfolio_returns.append(returns)
        if len(self.portfolio_returns) >= self.batch_size:
            self.flush_portfolio()

    def flush_risk(self):
        """Flush risk metrics"""
        for risk in self.risk_allocations:
            log_risk_allocation(risk)
        self.risk_allocations.clear()

    def flush_strategy(self):
        """Flush strategy metrics"""
        for deviation in self.strategy_deviations:
            log_strategy_deviation(deviation)
        self.strategy_deviations.clear()

    def flush_position(self):
        """Flush position metrics"""
        for velocity in self.position_velocities:
            log_position_velocity(velocity)
        self.position_velocities.clear()

    def flush_portfolio(self):
        """Flush portfolio metrics"""
        for returns in self.portfolio_returns:
            log_portfolio_return(returns)
        self.portfolio_returns.clear()

    def flush_all(self):
        """Flush all pending metrics"""
        self.flush_risk()
        self.flush_strategy()
        self.flush_position()
        self.flush_portfolio()


# Example usage
if __name__ == "__main__":
    print("Testing Financial Metrics...")

    # Log individual metrics
    print("\n1. Logging individual metrics:")
    log_risk_allocation(0.15, attributes={"cohort_id": 0})
    log_strategy_deviation(0.08, attributes={"cohort_id": 0})
    log_position_velocity(0.02, attributes={"cohort_id": 0})
    log_portfolio_return(0.0007, attributes={"day": 1})  # 0.07% daily return

    # Use batched collector
    print("\n2. Using batched collector:")
    collector = FinancialMetricsCollector(batch_size=10)

    for i in range(25):
        collector.add_risk_allocation(0.15 + i * 0.001)
        collector.add_strategy_deviation(0.08 + i * 0.0005)
        collector.add_position_velocity(0.02 + i * 0.0001)
        collector.add_portfolio_return(0.0007 + i * 0.00001)

    # Flush remaining
    collector.flush_all()

    print("\n✓ Financial Metrics tests passed")
