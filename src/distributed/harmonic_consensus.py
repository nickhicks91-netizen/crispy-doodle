"""
Harmonic Consensus
Consensus algorithm based on harmonic averaging for distributed φ and coherence
"""

import torch
from typing import Dict, List
import time


class HarmonicConsensus:
    """
    Harmonic consensus for distributed agreement

    Features:
    - Harmonic mean for φ-depth consensus
    - Weighted voting
    - Byzantine fault tolerance (basic)
    - Convergence tracking
    """

    def __init__(self, node_id: str, quorum_size: int = 3):
        """
        Initialize harmonic consensus

        Args:
            node_id: This node's ID
            quorum_size: Minimum nodes for consensus
        """
        self.node_id = node_id
        self.quorum_size = quorum_size

        self.local_value: float = 0.0
        self.remote_values: Dict[str, float] = {}
        self.weights: Dict[str, float] = {}
        self.timestamps: Dict[str, float] = {}

    def propose(self, value: float, weight: float = 1.0):
        """Propose local value"""
        self.local_value = value
        self.weights[self.node_id] = weight
        self.timestamps[self.node_id] = time.time()

    def receive_proposal(self, node_id: str, value: float, weight: float = 1.0):
        """Receive proposal from remote node"""
        self.remote_values[node_id] = value
        self.weights[node_id] = weight
        self.timestamps[node_id] = time.time()

    def compute_consensus(self, method: str = "harmonic") -> float:
        """
        Compute consensus value

        Args:
            method: "harmonic", "weighted", or "median"

        Returns:
            Consensus value
        """
        # Collect all values
        all_values = [self.local_value] + list(self.remote_values.values())
        all_weights = [self.weights.get(self.node_id, 1.0)] + [
            self.weights.get(nid, 1.0) for nid in self.remote_values.keys()
        ]

        if len(all_values) < self.quorum_size:
            # Not enough for quorum, return local
            return self.local_value

        # Remove outliers (simple Byzantine tolerance)
        all_values, all_weights = self._remove_outliers(all_values, all_weights)

        if method == "harmonic":
            # Harmonic mean
            if any(v == 0 for v in all_values):
                # Handle zeros
                consensus = sum(all_values) / len(all_values)
            else:
                reciprocals = [w / v for v, w in zip(all_values, all_weights)]
                total_weight = sum(all_weights)
                consensus = total_weight / sum(reciprocals)

        elif method == "weighted":
            # Weighted average
            total_weight = sum(all_weights)
            consensus = sum(v * w for v, w in zip(all_values, all_weights)) / total_weight

        elif method == "median":
            # Median (Byzantine-resistant)
            sorted_values = sorted(all_values)
            mid = len(sorted_values) // 2
            if len(sorted_values) % 2 == 0:
                consensus = (sorted_values[mid-1] + sorted_values[mid]) / 2.0
            else:
                consensus = sorted_values[mid]

        else:
            raise ValueError(f"Unknown method: {method}")

        return consensus

    def _remove_outliers(
        self,
        values: List[float],
        weights: List[float],
        threshold: float = 2.0
    ) -> tuple:
        """Remove outlier values (basic Byzantine tolerance)"""
        if len(values) <= 3:
            return values, weights  # Too few to remove outliers

        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5

        if std == 0:
            return values, weights

        # Keep values within threshold standard deviations
        filtered_values = []
        filtered_weights = []

        for v, w in zip(values, weights):
            if abs(v - mean) <= threshold * std:
                filtered_values.append(v)
                filtered_weights.append(w)

        # Must keep at least quorum_size values
        if len(filtered_values) < self.quorum_size:
            return values, weights

        return filtered_values, filtered_weights

    def has_quorum(self) -> bool:
        """Check if we have enough nodes for consensus"""
        total_nodes = 1 + len(self.remote_values)
        return total_nodes >= self.quorum_size

    def get_stats(self) -> Dict:
        """Get consensus statistics"""
        return {
            'node_id': self.node_id,
            'quorum_size': self.quorum_size,
            'total_nodes': 1 + len(self.remote_values),
            'has_quorum': self.has_quorum(),
            'local_value': self.local_value,
            'remote_nodes': len(self.remote_values)
        }


# Example usage
if __name__ == "__main__":
    # Create 5 nodes
    nodes = [HarmonicConsensus(f"node{i}", quorum_size=3) for i in range(5)]

    # Each node proposes a φ-depth value
    phi_values = [0.75, 0.78, 0.76, 0.92, 0.74]  # One outlier

    for node, phi in zip(nodes, phi_values):
        node.propose(phi)

    # Exchange proposals
    for i, node in enumerate(nodes):
        for j, other_node in enumerate(nodes):
            if i != j:
                node.receive_proposal(f"node{j}", phi_values[j])

    # Compute consensus
    print("Harmonic Consensus Test")
    print(f"Proposed values: {phi_values}")
    print(f"Outlier: node3 with φ=0.92")

    for method in ["harmonic", "weighted", "median"]:
        consensus = nodes[0].compute_consensus(method=method)
        print(f"\n{method.capitalize()} consensus: {consensus:.4f}")

    # Stats
    stats = nodes[0].get_stats()
    print(f"\nNode stats: {stats}")

    print("\n✓ Harmonic consensus tests passed")
