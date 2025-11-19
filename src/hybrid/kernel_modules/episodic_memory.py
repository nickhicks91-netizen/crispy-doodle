"""
Episodic Memory (v4.2.1)
-------------------------
Stores discrete episodes with temporal and contextual metadata.

Episodes include:
- ψ-state snapshot
- Qualia at time of episode
- φ-depth
- Contextual features
- Timestamp

Fixes from v4.2.0:
- Proper state management
- Efficient storage
"""

import torch
import torch.nn as nn
from typing import Dict, Optional, List
from collections import deque


class Episode:
    """Single episode representation."""

    def __init__(
        self,
        psi: torch.Tensor,
        qualia: torch.Tensor,
        phi: torch.Tensor,
        context: torch.Tensor,
        timestamp: int
    ):
        self.psi = psi.clone().detach()
        self.qualia = qualia.clone().detach()
        self.phi = phi.clone().detach()
        self.context = context.clone().detach()
        self.timestamp = timestamp


class EpisodicMemory(nn.Module):
    """
    Episodic memory storage and retrieval.
    """

    def __init__(
        self,
        max_episodes: int = 1000,
        episode_threshold: float = 0.7,  # φ threshold for storing episode
        device: Optional[str] = None
    ):
        """
        Args:
            max_episodes: Maximum number of episodes to store
            episode_threshold: Minimum φ to store episode
            device: Device to place on
        """
        super().__init__()

        self.max_episodes = max_episodes
        self.episode_threshold = episode_threshold

        # Episode storage (deque for efficient append/pop)
        self.episodes = deque(maxlen=max_episodes)

        # Episode counter
        self.register_buffer('episode_count', torch.tensor(0))

        # Retrieval network: query → episode similarity
        self.retriever = nn.Linear(4, 4)  # qualia → qualia similarity

        if device:
            self.to(device)

    def should_store(self, phi: torch.Tensor) -> bool:
        """
        Determine if current state should be stored as episode.

        Args:
            phi: Current φ value

        Returns:
            should_store: Whether to store
        """
        phi_val = phi.mean() if phi.numel() > 1 else phi
        return float(phi_val) > self.episode_threshold

    def store_episode(
        self,
        hybrid_out: Dict[str, torch.Tensor],
        context: torch.Tensor
    ):
        """
        Store new episode.

        Args:
            hybrid_out: Hybrid forward output
            context: Contextual features
        """
        episode = Episode(
            psi=hybrid_out['psi'],
            qualia=hybrid_out['qualia'],
            phi=hybrid_out['phi'],
            context=context,
            timestamp=int(self.episode_count)
        )

        self.episodes.append(episode)
        self.episode_count += 1

    def retrieve_similar(
        self,
        query_qualia: torch.Tensor,
        top_k: int = 5
    ) -> List[Episode]:
        """
        Retrieve episodes similar to query.

        Args:
            query_qualia: Query qualia [4]
            top_k: Number of episodes to retrieve

        Returns:
            episodes: List of similar episodes
        """
        if len(self.episodes) == 0:
            return []

        # Compute similarities
        similarities = []
        for ep in self.episodes:
            sim = torch.cosine_similarity(
                query_qualia.unsqueeze(0),
                ep.qualia.unsqueeze(0)
            )
            similarities.append((float(sim), ep))

        # Sort by similarity
        similarities.sort(key=lambda x: x[0], reverse=True)

        # Return top-k
        return [ep for _, ep in similarities[:top_k]]

    def forward(
        self,
        state: Dict[str, torch.Tensor],
        hybrid_out: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Manage episodic memory.

        Args:
            state: Current kernel state
            hybrid_out: Hybrid forward output

        Returns:
            Dictionary with episode_stored, retrieved_episodes
        """
        phi = hybrid_out['phi']
        qualia = hybrid_out['qualia']

        # Store episode if significant
        episode_stored = False
        if self.should_store(phi):
            # Use world state as context if available
            context = state.get('world_state', torch.zeros(32))
            self.store_episode(hybrid_out, context)
            episode_stored = True

        # Retrieve similar episodes
        retrieved = self.retrieve_similar(qualia, top_k=3)

        return {
            'episode_stored': episode_stored,
            'num_episodes': len(self.episodes),
            'retrieved_count': len(retrieved)
        }
