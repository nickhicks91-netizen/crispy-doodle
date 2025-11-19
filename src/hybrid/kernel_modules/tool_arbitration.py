"""
Tool Arbitration (v4.2.1)
--------------------------
Decides which cognitive tool or subsystem to activate based on current state.

Tools may include:
- Memory retrieval
- Scenario generation
- Predictive attention
- Meta-analysis

Fixes from v4.2.0:
- Proper state management
- Batching support
"""

import torch
import torch.nn as nn
from typing import Dict, Optional, List


class ToolArbitration(nn.Module):
    """
    Selects appropriate cognitive tool for current context.
    """

    def __init__(
        self,
        num_tools: int = 10,
        hidden_dim: int = 32,
        device: Optional[str] = None
    ):
        """
        Args:
            num_tools: Number of available tools
            hidden_dim: Hidden dimension for decision network
            device: Device to place on
        """
        super().__init__()

        self.num_tools = num_tools

        # Tool selection network
        # Input: phi, coherence_mean, qualia (4), align_mean = 7 features
        self.selector = nn.Sequential(
            nn.Linear(7, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_tools),
            nn.Softmax(dim=-1)
        )

        if device:
            self.to(device)

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Select tool based on current state.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with tool_probs, selected_tool
        """
        phi = hybrid_out['phi']
        coherence = hybrid_out['coherence']
        qualia = hybrid_out['qualia']
        align = hybrid_out.get('align', torch.zeros(8))

        # Handle batching
        unbatched = phi.ndim == 0
        if unbatched:
            phi = phi.unsqueeze(0)
            coherence = coherence.unsqueeze(0)
            qualia = qualia.unsqueeze(0)
            align = align.unsqueeze(0)

        # Create feature vector
        phi_feat = phi.unsqueeze(-1) if phi.ndim == 1 else phi
        coh_feat = coherence.mean(dim=-1, keepdim=True)
        align_feat = align.mean(dim=-1, keepdim=True)

        features = torch.cat([phi_feat, coh_feat, qualia, align_feat], dim=-1)

        # Select tool
        tool_probs = self.selector(features)
        selected_tool = torch.argmax(tool_probs, dim=-1)

        if unbatched:
            tool_probs = tool_probs.squeeze(0)
            selected_tool = selected_tool.squeeze(0)

        return {
            'tool_probs': tool_probs,
            'selected_tool': selected_tool
        }
