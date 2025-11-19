"""
Contextual Tool Policies (v4.2.1)
----------------------------------
Context-dependent policies for tool selection and use.

Learns:
- Which tools work best in which contexts
- Tool success rates
- Tool interaction patterns
- Resource-efficient tool scheduling

Fixes from v4.2.0:
- Proper state management
- Policy learning mechanisms
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class ContextualToolPolicies(nn.Module):
    """
    Context-aware tool selection policies.
    """

    def __init__(
        self,
        num_tools: int = 10,
        context_dim: int = 16,
        device: Optional[str] = None
    ):
        """
        Args:
            num_tools: Number of available tools
            context_dim: Context representation dimension
            device: Device to place on
        """
        super().__init__()

        self.num_tools = num_tools
        self.context_dim = context_dim

        # Context encoder
        # Input: phi(1) + coherence_mean(1) + qualia(4) + stress(1) + drift(1) = 8
        self.context_encoder = nn.Sequential(
            nn.Linear(8, context_dim),
            nn.ReLU(),
            nn.Tanh()
        )

        # Policy network: context → tool selection policy
        self.policy = nn.Sequential(
            nn.Linear(context_dim, 32),
            nn.ReLU(),
            nn.Linear(32, num_tools),
            nn.Softmax(dim=-1)
        )

        # Tool success tracker (buffer)
        self.register_buffer('tool_successes', torch.zeros(num_tools))
        self.register_buffer('tool_attempts', torch.zeros(num_tools))

        if device:
            self.to(device)

    def encode_context(
        self,
        hybrid_out: Dict[str, torch.Tensor],
        state: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        Encode current context.

        Args:
            hybrid_out: Hybrid forward output
            state: Kernel state

        Returns:
            context: Encoded context [context_dim]
        """
        phi = hybrid_out['phi']
        coherence = hybrid_out['coherence']
        qualia = hybrid_out['qualia']
        stress = state.get('stress_level', torch.tensor(0.0))
        drift = state.get('drift', torch.tensor(0.0))

        # Extract scalars
        phi_val = phi.mean() if phi.numel() > 1 else phi
        coh_val = coherence.mean()
        stress_val = stress.mean() if stress.numel() > 1 else stress
        drift_val = drift.mean() if drift.numel() > 1 else drift

        # Pad qualia if needed
        if qualia.numel() < 4:
            qualia = torch.nn.functional.pad(qualia, (0, 4 - qualia.numel()))

        # Concatenate features
        features = torch.cat([
            phi_val.unsqueeze(0) if phi_val.ndim == 0 else phi_val,
            coh_val.unsqueeze(0) if coh_val.ndim == 0 else coh_val,
            qualia[:4],
            stress_val.unsqueeze(0) if stress_val.ndim == 0 else stress_val,
            drift_val.unsqueeze(0) if drift_val.ndim == 0 else drift_val
        ])

        # Pad or truncate to 8 dims
        if features.numel() < 8:
            features = torch.nn.functional.pad(features, (0, 8 - features.numel()))
        else:
            features = features[:8]

        # Encode
        context = self.context_encoder(features)

        return context

    def select_tool(self, context: torch.Tensor) -> torch.Tensor:
        """
        Select tool based on context.

        Args:
            context: Encoded context

        Returns:
            policy: Tool selection probabilities [num_tools]
        """
        policy = self.policy(context)
        return policy

    def update_success(self, tool_id: int, success: bool):
        """
        Update tool success statistics.

        Args:
            tool_id: Tool index
            success: Whether tool use was successful
        """
        with torch.no_grad():
            self.tool_attempts[tool_id] += 1
            if success:
                self.tool_successes[tool_id] += 1

    def get_success_rate(self, tool_id: int) -> float:
        """
        Get success rate for a tool.

        Args:
            tool_id: Tool index

        Returns:
            success_rate: Success rate [0, 1]
        """
        attempts = float(self.tool_attempts[tool_id])
        if attempts == 0:
            return 0.5  # Default

        return float(self.tool_successes[tool_id]) / attempts

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Compute tool selection policy.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with context, policy, success_rates
        """
        # Encode context
        context = self.encode_context(hybrid_out, state)

        # Compute policy
        policy = self.select_tool(context)

        # Get success rates
        success_rates = torch.tensor([
            self.get_success_rate(i) for i in range(self.num_tools)
        ])

        return {
            'tool_context': context,
            'tool_policy': policy,
            'tool_success_rates': success_rates
        }
