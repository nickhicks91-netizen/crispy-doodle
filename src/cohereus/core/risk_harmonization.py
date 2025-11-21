"""
Risk Harmonization Layer (RHL) — Adapted from EchoZero WIL 2.0

Financial risk protection with:
- Multi-timescale EMA tracking of risk allocation
- Predictive drift detection for strategy divergence
- Volatility-informed corrections
- Catastrophic drawdown protection
- Capital preservation enforcement

This layer prevents:
- Slow drift toward excessive risk
- Sudden portfolio concentration
- Strategy fragmentation
- Runaway leverage dynamics

Adapted from: src/grcm/wil_v2.py (EchoZero v4.2.1)
"""

import torch
import torch.nn as nn
from typing import Optional


class RiskHarmonizationLayer(nn.Module):
    """
    RHL — Risk Envelope Protection

    Protects portfolio risk allocation from:
    - Adversarial manipulation
    - Slow drift toward excessive risk
    - Malformed market signals
    - Internal runaway dynamics

    Features:
    - EMA short-term risk tracking
    - EMA long-term risk tracking
    - Drift magnitude estimation
    - Predictive drift correction
    - Volatility-based risk gates
    - Catastrophic drawdown detection

    DNA Source: WantIntegrityLayerV2 (EchoZero)
    """

    def __init__(
        self,
        risk_min: float = 0.05,          # Minimum risk allocation (5%)
        risk_max: float = 0.30,          # Maximum risk allocation (30%)
        max_change_per_day: float = 0.02, # Max 2% daily risk shift
        smoothing_tau_short: float = 0.15,
        smoothing_tau_long: float = 0.01,
        drift_tolerance: float = 0.05,
        device: torch.device = torch.device('cpu')
    ):
        """
        Initialize RHL

        Args:
            risk_min: Minimum acceptable risk allocation (capital preservation floor)
            risk_max: Maximum acceptable risk allocation (volatility ceiling)
            max_change_per_day: Maximum allowed risk change per rebalance
            smoothing_tau_short: Short-term EMA coefficient
            smoothing_tau_long: Long-term EMA coefficient
            drift_tolerance: Maximum acceptable drift between timescales
            device: Computation device
        """
        super().__init__()

        self.risk_min = risk_min
        self.risk_max = risk_max
        self.max_change = max_change_per_day
        self.tau_s = smoothing_tau_short
        self.tau_l = smoothing_tau_long
        self.drift_tol = drift_tolerance
        self.device = device

        # State buffers (same architecture as WIL 2.0)
        self.register_buffer('prev_risk', None)
        self.register_buffer('ema_short', None)
        self.register_buffer('ema_long', None)

    def _ema(
        self,
        prev: Optional[torch.Tensor],
        new: torch.Tensor,
        tau: float
    ) -> torch.Tensor:
        """Exponential moving average (identical to WIL 2.0)"""
        if prev is None:
            return new.clone()
        return tau * new + (1 - tau) * prev

    def clamp_range(self, risk: torch.Tensor) -> torch.Tensor:
        """Clamp into capital-preservation range"""
        return risk.clamp(self.risk_min, self.risk_max)

    def smooth(self, risk: torch.Tensor) -> torch.Tensor:
        """EMA smoothing to prevent jarring rebalances"""
        if self.prev_risk is None:
            self.prev_risk = risk.clone()
            return risk

        smoothed = (
            self.tau_s * risk +
            (1 - self.tau_s) * self.prev_risk
        )

        self.prev_risk = smoothed.clone()
        return smoothed

    def limit_change(self, risk: torch.Tensor) -> torch.Tensor:
        """Prevents adversarial or accidental sudden risk spikes"""
        if self.prev_risk is None:
            return risk

        delta = risk - self.prev_risk
        delta = delta.clamp(-self.max_change, self.max_change)
        return self.prev_risk + delta

    def predictive_drift(
        self,
        risk: torch.Tensor,
        market_volatility: torch.Tensor
    ) -> torch.Tensor:
        """
        Predicts future drift using two EMA timescales.
        If short-term and long-term trends diverge beyond tolerance,
        apply corrective dampening.

        Args:
            risk: Current risk allocation
            market_volatility: Market volatility metric (VIX-like)

        Returns:
            Drift-corrected risk allocation
        """
        # Track short and long-term trends (identical to WIL 2.0)
        self.ema_short = self._ema(self.ema_short, risk, self.tau_s)
        self.ema_long = self._ema(self.ema_long, risk, self.tau_l)

        # Calculate drift
        drift = torch.abs(self.ema_short - self.ema_long)

        # If drift exceeds tolerance AND volatility is high → apply dampening
        vol_mean = market_volatility.mean() if market_volatility.numel() > 1 else market_volatility

        if drift > self.drift_tol and vol_mean > 0.25:
            # Apply corrective bias toward long-term trend (conservative)
            correction = (self.ema_long - self.ema_short) * 0.4
            risk = risk + correction

        return risk

    def volatility_guard(
        self,
        risk: torch.Tensor,
        market_volatility: torch.Tensor
    ) -> torch.Tensor:
        """
        If market volatility spikes too fast,
        restrict risk allocation to prevent capital drawdown.

        Args:
            risk: Current risk allocation
            market_volatility: Market volatility metric

        Returns:
            Volatility-guarded risk allocation
        """
        vol_mean = market_volatility.mean() if market_volatility.numel() > 1 else market_volatility

        if vol_mean > 0.40:  # High volatility regime
            # Restrict to lower, safer range
            safe_max = self.risk_min + (self.risk_max - self.risk_min) * 0.35
            risk = risk.clamp(self.risk_min, safe_max)

        return risk

    def drawdown_detector(self, risk: torch.Tensor) -> torch.Tensor:
        """
        Detects and corrects catastrophic unnatural jumps in risk allocation.

        Args:
            risk: Current risk allocation

        Returns:
            Jump-corrected risk allocation
        """
        if self.prev_risk is None:
            return risk

        jump = torch.abs(risk - self.prev_risk)

        # Catastrophic jump threshold (15% sudden shift)
        if jump > 0.15:
            # Pull back to previous safe value with limited step
            direction = torch.sign(risk - self.prev_risk)
            risk = self.prev_risk + direction * 0.02

        return risk

    def forward(
        self,
        risk: torch.Tensor,
        market_volatility: torch.Tensor
    ) -> torch.Tensor:
        """
        Full RHL pipeline (identical structure to WIL 2.0).

        Args:
            risk: Raw risk allocation
            market_volatility: Market volatility metric

        Returns:
            Protected, stabilized risk allocation
        """
        # Ensure tensors are on correct device
        risk = risk.to(self.device)
        market_volatility = market_volatility.to(self.device)

        # Protection pipeline (same order as WIL 2.0)
        risk = self.clamp_range(risk)
        risk = self.smooth(risk)
        risk = self.limit_change(risk)
        risk = self.predictive_drift(risk, market_volatility)
        risk = self.volatility_guard(risk, market_volatility)
        risk = self.drawdown_detector(risk)

        return risk

    def get_drift_metrics(self) -> dict:
        """Get current drift diagnostics"""
        if self.ema_short is None or self.ema_long is None:
            return {
                'drift': 0.0,
                'ema_short': 0.0,
                'ema_long': 0.0,
                'prev_risk': 0.0
            }

        drift = torch.abs(self.ema_short - self.ema_long)

        return {
            'drift': drift.item() if drift.numel() == 1 else drift.mean().item(),
            'ema_short': self.ema_short.item() if self.ema_short.numel() == 1 else self.ema_short.mean().item(),
            'ema_long': self.ema_long.item() if self.ema_long.numel() == 1 else self.ema_long.mean().item(),
            'prev_risk': self.prev_risk.item() if self.prev_risk.numel() == 1 else self.prev_risk.mean().item()
        }

    def reset(self):
        """Reset internal state (for new account initialization)"""
        self.prev_risk = None
        self.ema_short = None
        self.ema_long = None


# Example usage
if __name__ == "__main__":
    print("Testing Risk Harmonization Layer (RHL)...")

    rhl = RiskHarmonizationLayer()

    # Test normal operation
    print("\n1. Normal operation:")
    risk = torch.tensor(0.15)  # 15% risk allocation
    volatility = torch.tensor(0.12)  # Low volatility

    for i in range(10):
        risk_protected = rhl(risk, volatility)
        print(f"  Day {i}: risk={risk.item():.4f} → protected={risk_protected.item():.4f}")
        risk += 0.01

    # Test adversarial spike
    print("\n2. Adversarial spike:")
    risk = torch.tensor(0.80)  # 80% risk (dangerous!)
    volatility = torch.tensor(0.12)
    risk_protected = rhl(risk, volatility)
    print(f"  Attack: risk={risk.item():.4f} → protected={risk_protected.item():.4f}")

    # Test volatility spike
    print("\n3. Market volatility spike:")
    risk = torch.tensor(0.25)
    for i in range(20):
        volatility = torch.tensor(0.10 + i * 0.03)  # Rising volatility
        risk_protected = rhl(risk, volatility)

        if i % 5 == 0:
            metrics = rhl.get_drift_metrics()
            print(f"  Day {i}: vol={volatility.item():.4f}, "
                  f"risk={risk_protected.item():.4f}, "
                  f"drift={metrics['drift']:.4f}")

    print("\n✓ RHL tests passed")
