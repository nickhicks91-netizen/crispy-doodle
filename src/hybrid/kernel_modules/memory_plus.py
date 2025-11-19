"""
Memory+ (v4.2.1)
----------------
Enhanced memory system with:
- Long-term memory consolidation
- Working memory prioritization
- Memory retrieval mechanisms

Extends the base GRU memory module.

Fixes from v4.2.0:
- Functional updates (no mutation)
- Batching support
- Device management
"""

import torch
import torch.nn as nn
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple


def load_dims():
    config_path = Path(__file__).parent.parent.parent / "config" / "dimensions.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

DIMS = load_dims()


class MemoryPlus(nn.Module):
    """
    Enhanced memory system with long-term and working memory separation.
    """

    def __init__(
        self,
        mem_dim: Optional[int] = None,
        working_dim: int = 64,
        device: Optional[str] = None
    ):
        """
        Args:
            mem_dim: Long-term memory dimension (default from config)
            working_dim: Working memory dimension
            device: Device to place on
        """
        super().__init__()

        self.mem_dim = mem_dim or DIMS['memory_dim']
        self.working_dim = working_dim

        # Working memory attention
        self.attention = nn.MultiheadAttention(
            embed_dim=self.mem_dim,
            num_heads=4,
            batch_first=True
        )

        # Consolidation network: working → long-term
        self.consolidator = nn.Linear(self.working_dim, self.mem_dim)

        # Retrieval network: query → retrieved memory
        self.retriever = nn.Linear(self.mem_dim, self.mem_dim)

        if device:
            self.to(device)

    def retrieve(
        self,
        query: torch.Tensor,
        long_term_memory: torch.Tensor
    ) -> torch.Tensor:
        """
        Retrieve relevant memory based on query.

        Args:
            query: Query vector [mem_dim] or [batch, mem_dim]
            long_term_memory: Long-term memory [mem_dim] or [batch, mem_dim]

        Returns:
            retrieved: Retrieved memory
        """
        # Handle batching
        unbatched = query.ndim == 1
        if unbatched:
            query = query.unsqueeze(0)
            long_term_memory = long_term_memory.unsqueeze(0)

        # Simple retrieval via linear transformation
        retrieved = self.retriever(long_term_memory)

        # Weight by query similarity
        similarity = torch.cosine_similarity(query, retrieved, dim=-1, keepdim=True)
        retrieved = retrieved * torch.sigmoid(similarity)

        if unbatched:
            retrieved = retrieved.squeeze(0)

        return retrieved

    def consolidate(
        self,
        working_memory: torch.Tensor,
        long_term_memory: torch.Tensor,
        consolidation_rate: float = 0.1
    ) -> torch.Tensor:
        """
        Consolidate working memory into long-term memory.

        Args:
            working_memory: Working memory [working_dim] or [batch, working_dim]
            long_term_memory: Long-term memory [mem_dim] or [batch, mem_dim]
            consolidation_rate: Rate of consolidation

        Returns:
            updated_ltm: Updated long-term memory
        """
        # Handle batching
        unbatched = working_memory.ndim == 1
        if unbatched:
            working_memory = working_memory.unsqueeze(0)
            long_term_memory = long_term_memory.unsqueeze(0)

        # Project working memory to long-term space
        consolidated = self.consolidator(working_memory)

        # Blend with existing long-term memory
        updated_ltm = (1 - consolidation_rate) * long_term_memory + consolidation_rate * consolidated

        if unbatched:
            updated_ltm = updated_ltm.squeeze(0)

        return updated_ltm

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Process memory operations.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with memory_retrieval, memory_consolidation
        """
        memory = hybrid_out['memory']

        # Use phi as working memory proxy
        phi = hybrid_out['phi']
        if phi.ndim == 0:
            phi = phi.unsqueeze(0)

        # Create working memory representation
        working = phi.unsqueeze(-1).repeat(1, self.working_dim) if phi.ndim == 1 else phi

        # Retrieve relevant memories
        retrieved = self.retrieve(memory, memory)

        # Consolidate if needed (based on phi threshold)
        if torch.mean(phi) > 0.5:
            consolidated = self.consolidate(working, memory)
        else:
            consolidated = memory

        return {
            'memory_retrieval': retrieved,
            'memory_consolidation': consolidated
        }
