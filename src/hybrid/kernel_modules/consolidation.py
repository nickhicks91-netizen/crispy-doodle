"""
Memory Consolidation (Sleep Mode) (v4.2.1)
-------------------------------------------
Consolidates memories during low-activity periods.

Consolidation process:
- Transfers important patterns from working to long-term memory
- Prunes redundant memories
- Strengthens frequently accessed patterns
- Reorganizes memory structure

Triggers:
- High stress levels
- High drift
- Explicit sleep signal

Fixes from v4.2.0:
- Proper state management
- Efficient consolidation algorithms
"""

import torch
import torch.nn as nn
from typing import Dict, Optional


class MemoryConsolidation(nn.Module):
    """
    Sleep-like memory consolidation process.
    """

    def __init__(
        self,
        consolidation_threshold: float = 0.7,  # Stress threshold
        consolidation_rate: float = 0.3,
        device: Optional[str] = None
    ):
        """
        Args:
            consolidation_threshold: Stress threshold for triggering consolidation
            consolidation_rate: Rate of memory consolidation
            device: Device to place on
        """
        super().__init__()

        self.consolidation_threshold = consolidation_threshold
        self.consolidation_rate = consolidation_rate

        # Consolidation network: memory → consolidated memory
        self.consolidator = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.Tanh()
        )

        # Pruning network: decides what to keep
        self.pruner = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.Sigmoid()  # Importance mask
        )

        if device:
            self.to(device)

    def should_consolidate(
        self,
        stress: torch.Tensor,
        drift: torch.Tensor
    ) -> bool:
        """
        Determine if consolidation should be triggered.

        Args:
            stress: Current stress level
            drift: Current drift

        Returns:
            should_consolidate: Whether to consolidate
        """
        stress_val = stress.mean() if stress.numel() > 1 else stress
        drift_val = drift.mean() if drift.numel() > 1 else drift

        # Consolidate if either stress or drift is high
        return (float(stress_val) > self.consolidation_threshold) or \
               (float(drift_val) > 0.5)

    def consolidate_memory(self, memory: torch.Tensor) -> torch.Tensor:
        """
        Perform consolidation.

        Args:
            memory: Current memory state

        Returns:
            consolidated: Consolidated memory
        """
        # Ensure size
        if memory.numel() > 128:
            memory = memory[:128]
        elif memory.numel() < 128:
            memory = torch.nn.functional.pad(memory, (0, 128 - memory.numel()))

        # Apply consolidation
        consolidated = self.consolidator(memory)

        # Apply pruning (keep important parts)
        importance = self.pruner(memory)
        consolidated = consolidated * importance

        return consolidated

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Manage consolidation process.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with consolidation_performed, consolidated_memory
        """
        memory = hybrid_out['memory']
        stress = state.get('stress_level', torch.tensor(0.0))
        drift = state.get('drift', torch.tensor(0.0))

        # Check if consolidation needed
        should_consolidate = self.should_consolidate(stress, drift)

        consolidated_memory = memory
        consolidation_performed = False

        if should_consolidate:
            consolidated_memory = self.consolidate_memory(memory)
            consolidation_performed = True

        return {
            'consolidation_performed': consolidation_performed,
            'consolidated_memory': consolidated_memory
        }
