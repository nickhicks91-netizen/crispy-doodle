"""
Working Memory Rehearsal (v4.2.1)
----------------------------------
Reinforces important patterns in working memory through rehearsal.

Rehearsal strategies:
- Replay high-φ states
- Strengthen goal-aligned patterns
- Consolidate successful episodes

Fixes from v4.2.0:
- Proper state management
- Efficient rehearsal scheduling
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class WorkingMemoryRehearsal(nn.Module):
    """
    Rehearsal mechanism for working memory consolidation.
    """

    def __init__(
        self,
        rehearsal_rate: float = 0.1,
        replay_strength: float = 0.2,
        device: Optional[str] = None
    ):
        """
        Args:
            rehearsal_rate: Probability of rehearsal on each step
            replay_strength: Strength of rehearsal updates
            device: Device to place on
        """
        super().__init__()

        self.rehearsal_rate = rehearsal_rate
        self.replay_strength = replay_strength

        # Rehearsal buffer (stores patterns to reinforce)
        self.register_buffer('rehearsal_buffer', torch.zeros(10, 128))  # 10 patterns x 128 dim
        self.register_buffer('buffer_idx', torch.tensor(0))
        self.register_buffer('buffer_importance', torch.zeros(10))  # Importance scores

        # Importance scorer
        self.importance_net = nn.Linear(4, 1)  # qualia → importance

        if device:
            self.to(device)

    def compute_importance(self, qualia: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
        """
        Compute importance of current state for rehearsal.

        Args:
            qualia: Qualia distribution [4]
            phi: φ-depth

        Returns:
            importance: Importance score
        """
        # Pad qualia if needed
        if qualia.numel() < 4:
            qualia = torch.nn.functional.pad(qualia, (0, 4 - qualia.numel()))

        # Importance based on qualia
        qualia_importance = self.importance_net(qualia[:4])

        # Boost by φ
        phi_val = phi.mean() if phi.numel() > 1 else phi
        importance = qualia_importance.squeeze() * torch.sigmoid(phi_val)

        return importance

    def add_to_buffer(
        self,
        memory: torch.Tensor,
        importance: torch.Tensor
    ):
        """
        Add pattern to rehearsal buffer.

        Args:
            memory: Memory vector to store
            importance: Importance score
        """
        idx = int(self.buffer_idx % 10)

        # Ensure memory is correct size
        if memory.numel() > 128:
            memory = memory[:128]
        elif memory.numel() < 128:
            memory = torch.nn.functional.pad(memory, (0, 128 - memory.numel()))

        self.rehearsal_buffer[idx] = memory.detach()
        self.buffer_importance[idx] = importance.detach()
        self.buffer_idx += 1

    def rehearse(self, current_memory: torch.Tensor) -> torch.Tensor:
        """
        Perform rehearsal by blending current memory with buffered patterns.

        Args:
            current_memory: Current memory state

        Returns:
            rehearsed_memory: Memory after rehearsal
        """
        if self.buffer_idx == 0:
            return current_memory

        # Get most important pattern from buffer
        most_important_idx = torch.argmax(self.buffer_importance)
        important_pattern = self.rehearsal_buffer[most_important_idx]

        # Ensure size match
        if important_pattern.numel() > current_memory.numel():
            important_pattern = important_pattern[:current_memory.numel()]
        elif important_pattern.numel() < current_memory.numel():
            important_pattern = torch.nn.functional.pad(
                important_pattern,
                (0, current_memory.numel() - important_pattern.numel())
            )

        # Blend with current memory
        rehearsed = (1 - self.replay_strength) * current_memory + \
                    self.replay_strength * important_pattern

        return rehearsed

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Manage rehearsal process.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with rehearsal_performed, rehearsed_memory
        """
        qualia = hybrid_out['qualia']
        phi = hybrid_out['phi']
        memory = hybrid_out['memory']

        # Compute importance
        importance = self.compute_importance(qualia, phi)

        # Add to buffer if important
        if float(importance) > 0.5:
            self.add_to_buffer(memory, importance)

        # Perform rehearsal with probability rehearsal_rate
        rehearsal_performed = False
        rehearsed_memory = memory

        if torch.rand(1).item() < self.rehearsal_rate:
            rehearsed_memory = self.rehearse(memory)
            rehearsal_performed = True

        return {
            'rehearsal_performed': rehearsal_performed,
            'rehearsed_memory': rehearsed_memory,
            'buffer_size': int(min(self.buffer_idx, 10))
        }
