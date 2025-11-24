"""
CO-HERE-US Unity v1.0 - Fracton Mode

Implements 5% dampening on NEGATIVE returns only.
Provides stability during downturns without suppressing positive growth.
"""

import numpy as np
from typing import Union, List

from .config import FRACTON_DAMP


def fracton_mode(returns: Union[np.ndarray, List[float]]) -> np.ndarray:
    """
    Fracton Mode — Dampens ONLY negative swings by 5%.

    Positive returns pass through unchanged.
    Negative returns are reduced by 5% (made less negative).

    Formula:
        if return < 0:
            dampened = return * (1 - FRACTON_DAMP) = return * 0.95
        else:
            dampened = return (unchanged)

    Examples:
        -10% return → -9.5% (dampened)
        +15% return → +15% (unchanged)

    Args:
        returns: Array or list of annual returns

    Returns:
        np.ndarray: Returns with negative values dampened
    """
    returns = np.asarray(returns)
    damped = np.where(returns < 0, returns * (1 - FRACTON_DAMP), returns)
    return damped


class FractonController:
    """
    Fracton Mode Controller.

    Manages dampening of negative returns while preserving positive growth.
    """

    def __init__(self, damp_strength: float = FRACTON_DAMP):
        """
        Initialize Fracton controller.

        Args:
            damp_strength: Dampening strength for negative returns (0-1).
                          Default is 0.05 (5% dampening)
        """
        if not 0 <= damp_strength <= 1:
            raise ValueError("Fracton damp strength must be between 0 and 1")
        self.damp_strength = damp_strength

    def dampen(self, returns: Union[np.ndarray, List[float]]) -> np.ndarray:
        """
        Apply Fracton dampening to a sequence of returns.

        Only negative returns are dampened. Positive returns pass through unchanged.

        Args:
            returns: Array or list of returns

        Returns:
            np.ndarray: Returns with negative values dampened
        """
        returns = np.asarray(returns)
        damped = np.where(returns < 0, returns * (1 - self.damp_strength), returns)
        return damped

    def dampen_single(self, return_value: float) -> float:
        """
        Dampen a single return if negative.

        Args:
            return_value: The return to potentially dampen

        Returns:
            float: Dampened return (if negative) or original return (if positive)
        """
        if return_value < 0:
            return return_value * (1 - self.damp_strength)
        return return_value

    def get_damp_strength(self) -> float:
        """Get the current Fracton dampening strength."""
        return self.damp_strength

    def set_damp_strength(self, damp_strength: float):
        """
        Set the Fracton dampening strength.

        Args:
            damp_strength: New strength value (0-1)
        """
        if not 0 <= damp_strength <= 1:
            raise ValueError("Fracton damp strength must be between 0 and 1")
        self.damp_strength = damp_strength

    def __repr__(self) -> str:
        return f"FractonController(damp_strength={self.damp_strength:.2%})"
