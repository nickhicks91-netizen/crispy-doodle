"""
ODE Solver for EchoZero Dynamics (v4.2.1)
------------------------------------------
Provides:
- RK4 integration for complex-valued ODEs
- Batched evolution
- Error handling

Fixes: Proper batching, convergence checks
"""

import torch
from typing import Callable, Tuple, Any
from ..core.errors import ConvergenceError


def rk4_step(
    func: Callable,
    psi: torch.Tensor,
    dt: float,
    *args: Any
) -> torch.Tensor:
    """
    Performs one RK4 step for ψ̇ = f(ψ, t).

    Args:
        func: Dynamics function (ψ, *args) -> ψ̇
        psi: Complex state vector [N] or [batch, N]
        dt: Step size
        args: Additional inputs (I_t, desires, node_freqs)

    Returns:
        psi_next: Updated state
    """
    k1 = func(psi, *args)
    k2 = func(psi + 0.5 * dt * k1, *args)
    k3 = func(psi + 0.5 * dt * k2, *args)
    k4 = func(psi + dt * k3, *args)

    psi_next = psi + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    # Convergence check
    if torch.any(torch.isnan(psi_next)) or torch.any(torch.isinf(psi_next)):
        raise ConvergenceError("ODE integration produced NaN or Inf")

    return psi_next


def integrate(
    func: Callable,
    psi0: torch.Tensor,
    t_span: Tuple[float, float],
    dt: float,
    *args: Any
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Integrate ODE over time interval.

    Args:
        func: Dynamics function
        psi0: Initial state
        t_span: (t_start, t_end)
        dt: Time step
        args: Additional arguments to func

    Returns:
        t: Time points [num_steps]
        psi: States [num_steps, N] or [num_steps, batch, N]
    """
    t_start, t_end = t_span
    num_steps = int((t_end - t_start) / dt)

    # Storage
    t_values = torch.linspace(t_start, t_end, num_steps)
    psi_values = torch.zeros(num_steps, *psi0.shape, dtype=psi0.dtype, device=psi0.device)

    psi = psi0.clone()
    psi_values[0] = psi

    for i in range(1, num_steps):
        psi = rk4_step(func, psi, dt, *args)
        psi_values[i] = psi

    return t_values, psi_values
