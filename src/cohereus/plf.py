"""
CO-HERE-US Unity v1.0 - Phase-Locked Framework (PLF) 2.0

Implements 35% smoothing toward mean, preserving 65% of original growth.
This prevents extreme volatility without suppressing long-term returns.
"""

import numpy as np
from typing import Union, List

from .config import PLF_STRENGTH


def plf_smoothing(returns: Union[np.ndarray, List[float]]) -> np.ndarray:
    """
    PLF 2.0 — 35% pull toward mean, 65% original value.

    This smoothing reduces volatility while preserving the expected return
    over time. It prevents extreme swings without dampening growth.

    Formula:
        smoothed_return = original_return * (1 - PLF_STRENGTH) + mean * PLF_STRENGTH
        smoothed_return = original_return * 0.65 + mean * 0.35

    Args:
        returns: Array or list of annual returns

    Returns:
        np.ndarray: Smoothed returns with same mean but reduced volatility
    """
    returns = np.asarray(returns)
    mean_r = np.mean(returns)
    smoothed = returns * (1 - PLF_STRENGTH) + mean_r * PLF_STRENGTH
    return smoothed


class PLFController:
    """
    Phase-Locked Framework Controller.

    Manages PLF smoothing operations for return sequences.
    """

    def __init__(self, strength: float = PLF_STRENGTH):
        """
        Initialize PLF controller.

        Args:
            strength: Smoothing strength (0-1). Default is 0.35 (35% smoothing)
        """
        if not 0 <= strength <= 1:
            raise ValueError("PLF strength must be between 0 and 1")
        self.strength = strength

    def smooth(self, returns: Union[np.ndarray, List[float]]) -> np.ndarray:
        """
        Apply PLF smoothing to a sequence of returns.

        Args:
            returns: Array or list of returns

        Returns:
            np.ndarray: Smoothed returns
        """
        returns = np.asarray(returns)
        mean_r = np.mean(returns)
        smoothed = returns * (1 - self.strength) + mean_r * self.strength
        return smoothed

    def smooth_single(self, return_value: float, reference_mean: float) -> float:
        """
        Smooth a single return toward a reference mean.

        Args:
            return_value: The return to smooth
            reference_mean: The mean to smooth toward

        Returns:
            float: Smoothed return
        """
        return return_value * (1 - self.strength) + reference_mean * self.strength

    def get_strength(self) -> float:
        """Get the current PLF smoothing strength."""
        return self.strength

    def set_strength(self, strength: float):
        """
        Set the PLF smoothing strength.

        Args:
            strength: New strength value (0-1)
        """
        if not 0 <= strength <= 1:
            raise ValueError("PLF strength must be between 0 and 1")
        self.strength = strength

    def __repr__(self) -> str:
        return f"PLFController(strength={self.strength:.2%})"
