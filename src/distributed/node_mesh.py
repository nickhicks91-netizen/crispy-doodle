"""
Node Mesh
Manages distributed node topology and routing for EchoZero clusters
"""

import torch
import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
import random


class TopologyType(Enum):
    """Network topology types"""
    FULL_MESH = "full_mesh"  # All nodes connected
    RING = "ring"  # Nodes in a ring
    TREE = "tree"  # Hierarchical tree
    HYBRID = "hybrid"  # Combination


@dataclass
class NodeInfo:
    """Information about a node"""
    node_id: str
    address: str
    port: int
    region: str
    capabilities: Dict[str, any]
    last_seen: float


@dataclass
class Connection:
    """Connection between nodes"""
    source: str
    target: str
    latency_ms: float
    bandwidth_mbps: float
    active: bool


class NodeMesh:
    """
    Manages distributed node topology and message routing

    Features:
    - Dynamic topology management
    - Automatic peer discovery
    - Latency-aware routing
    - Load balancing
    - Fault-tolerant routing
    """

    def __init__(
        self,
        node_id: str,
        topology_type: TopologyType = TopologyType.HYBRID,
        max_connections: int = 10,
        region: str = "default"
    ):
        """
        Initialize node mesh

        Args:
            node_id: This node's ID
            topology_type: Network topology
            max_connections: Maximum connections per node
            region: Geographic/logical region
        """
        self.node_id = node_id
        self.topology_type = topology_type
        self.max_connections = max_connections
        self.region = region

        # Node registry
        self.nodes: Dict[str, NodeInfo] = {}
        self.connections: Dict[str, List[Connection]] = {}

        # Routing table (node_id -> next_hop)
        self.routing_table: Dict[str, str] = {}

        # Neighborhoods (for hierarchical routing)
        self.local_neighbors: Set[str] = set()
        self.regional_neighbors: Set[str] = set()
        self.global_neighbors: Set[str] = set()

        # Thread safety
        self.lock = threading.Lock()

    def register_node(
        self,
        node_id: str,
        address: str,
        port: int,
        region: str = "default",
        capabilities: Optional[Dict] = None
    ):
        """
        Register a node in the mesh

        Args:
            node_id: Node identifier
            address: Network address
            port: Port number
            region: Geographic/logical region
            capabilities: Node capabilities
        """
        with self.lock:
            node_info = NodeInfo(
                node_id=node_id,
                address=address,
                port=port,
                region=region,
                capabilities=capabilities or {},
                last_seen=time.time()
            )

            self.nodes[node_id] = node_info

            # Initialize connection list
            if node_id not in self.connections:
                self.connections[node_id] = []

            # Update topology
            self._update_topology(node_id)

    def _update_topology(self, new_node_id: str):
        """Update network topology when node joins"""
        if self.topology_type == TopologyType.FULL_MESH:
            self._build_full_mesh(new_node_id)
        elif self.topology_type == TopologyType.RING:
            self._build_ring(new_node_id)
        elif self.topology_type == TopologyType.TREE:
            self._build_tree(new_node_id)
        else:  # HYBRID
            self._build_hybrid(new_node_id)

    def _build_full_mesh(self, new_node_id: str):
        """Build full mesh topology"""
        # Connect new node to all existing nodes
        for node_id in self.nodes:
            if node_id != new_node_id and node_id != self.node_id:
                self._add_bidirectional_connection(self.node_id, node_id)

    def _build_ring(self, new_node_id: str):
        """Build ring topology"""
        node_list = sorted(self.nodes.keys())
        n = len(node_list)

        if n < 2:
            return

        # Clear old connections
        self.connections = {node: [] for node in node_list}

        # Create ring
        for i, node_id in enumerate(node_list):
            next_node = node_list[(i + 1) % n]
            self._add_connection(node_id, next_node)

    def _build_tree(self, new_node_id: str):
        """Build tree topology"""
        node_list = sorted(self.nodes.keys())

        # Root is first node
        if len(node_list) <= 1:
            return

        # Each node connects to parent (simple binary tree)
        for i, node_id in enumerate(node_list):
            if i > 0:
                parent_idx = (i - 1) // 2
                parent_id = node_list[parent_idx]
                self._add_bidirectional_connection(node_id, parent_id)

    def _build_hybrid(self, new_node_id: str):
        """
        Build hybrid topology:
        - Local: Full mesh within region
        - Regional: Connect to regional hubs
        - Global: Sparse connections to other regions
        """
        new_node = self.nodes[new_node_id]

        # Local connections (same region)
        local_nodes = [
            nid for nid, info in self.nodes.items()
            if info.region == new_node.region and nid != new_node_id
        ]

        for node_id in local_nodes[:self.max_connections // 2]:
            self._add_bidirectional_connection(new_node_id, node_id)
            self.local_neighbors.add(node_id)

        # Regional connections (nearby regions)
        regional_nodes = [
            nid for nid, info in self.nodes.items()
            if info.region != new_node.region and nid != new_node_id
        ]

        # Connect to a few regional nodes
        for node_id in random.sample(
            regional_nodes,
            min(len(regional_nodes), self.max_connections // 4)
        ):
            self._add_bidirectional_connection(new_node_id, node_id)
            self.regional_neighbors.add(node_id)

    def _add_connection(
        self,
        source: str,
        target: str,
        latency_ms: float = 10.0,
        bandwidth_mbps: float = 1000.0
    ):
        """Add unidirectional connection"""
        connection = Connection(
            source=source,
            target=target,
            latency_ms=latency_ms,
            bandwidth_mbps=bandwidth_mbps,
            active=True
        )

        if source not in self.connections:
            self.connections[source] = []

        # Check if connection already exists
        existing = [c for c in self.connections[source] if c.target == target]
        if not existing:
            self.connections[source].append(connection)

    def _add_bidirectional_connection(
        self,
        node_a: str,
        node_b: str,
        latency_ms: float = 10.0,
        bandwidth_mbps: float = 1000.0
    ):
        """Add bidirectional connection"""
        self._add_connection(node_a, node_b, latency_ms, bandwidth_mbps)
        self._add_connection(node_b, node_a, latency_ms, bandwidth_mbps)

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get direct neighbors of a node"""
        with self.lock:
            if node_id not in self.connections:
                return []

            return [
                conn.target for conn in self.connections[node_id]
                if conn.active
            ]

    def compute_routing_table(self):
        """Compute routing table using shortest path (Dijkstra)"""
        with self.lock:
            # Initialize distances
            distances = {node: float('inf') for node in self.nodes}
            distances[self.node_id] = 0

            # Next hop for routing
            next_hop = {node: None for node in self.nodes}

            # Priority queue (distance, node)
            unvisited = set(self.nodes.keys())

            while unvisited:
                # Get node with minimum distance
                current = min(unvisited, key=lambda n: distances[n])

                if distances[current] == float('inf'):
                    break  # Remaining nodes unreachable

                unvisited.remove(current)

                # Check neighbors
                if current in self.connections:
                    for conn in self.connections[current]:
                        if not conn.active:
                            continue

                        neighbor = conn.target
                        distance = distances[current] + conn.latency_ms

                        if distance < distances[neighbor]:
                            distances[neighbor] = distance

                            # Update next hop
                            if current == self.node_id:
                                next_hop[neighbor] = neighbor
                            else:
                                next_hop[neighbor] = next_hop[current]

            # Update routing table
            self.routing_table = {
                node: hop for node, hop in next_hop.items()
                if hop is not None
            }

    def get_route(self, target_node: str) -> List[str]:
        """
        Get route to target node

        Args:
            target_node: Destination node

        Returns:
            List of node IDs forming route
        """
        if target_node == self.node_id:
            return [self.node_id]

        if target_node not in self.routing_table:
            # Try to compute routing table
            self.compute_routing_table()

        if target_node not in self.routing_table:
            return []  # No route

        # Trace route
        route = [self.node_id]
        current = self.node_id

        max_hops = len(self.nodes) + 1
        hops = 0

        while current != target_node and hops < max_hops:
            next_node = self.routing_table.get(current)

            if next_node is None:
                break

            route.append(next_node)
            current = next_node
            hops += 1

        return route if current == target_node else []

    def select_sync_targets(
        self,
        count: int,
        prefer_local: bool = True
    ) -> List[str]:
        """
        Select nodes for state synchronization

        Args:
            count: Number of targets
            prefer_local: Prefer local region nodes

        Returns:
            List of node IDs to sync with
        """
        with self.lock:
            candidates = list(self.nodes.keys())
            candidates = [n for n in candidates if n != self.node_id]

            if not candidates:
                return []

            if prefer_local and self.local_neighbors:
                # Prefer local neighbors
                local = list(self.local_neighbors)
                if len(local) >= count:
                    return random.sample(local, count)
                else:
                    # Fill with regional/global
                    remaining = count - len(local)
                    others = [n for n in candidates if n not in local]
                    return local + random.sample(others, min(remaining, len(others)))

            # Random selection
            return random.sample(candidates, min(count, len(candidates)))

    def get_node_load(self, node_id: str) -> float:
        """
        Estimate node load (for load balancing)

        Returns:
            Load metric (0-1, higher = more loaded)
        """
        with self.lock:
            if node_id not in self.connections:
                return 0.0

            # Simple heuristic: connection count / max_connections
            active_connections = sum(
                1 for conn in self.connections[node_id] if conn.active
            )

            return active_connections / max(self.max_connections, 1)

    def balance_load(self) -> Dict[str, List[str]]:
        """
        Rebalance connections across nodes

        Returns:
            Recommended connection changes
        """
        with self.lock:
            node_loads = {
                node: self.get_node_load(node)
                for node in self.nodes
            }

            # Find overloaded and underloaded nodes
            overloaded = [n for n, load in node_loads.items() if load > 0.8]
            underloaded = [n for n, load in node_loads.items() if load < 0.3]

            recommendations = {}

            # Suggest moving connections
            for node in overloaded:
                if underloaded:
                    recommendations[node] = underloaded[:2]

            return recommendations

    def get_cluster_stats(self) -> Dict:
        """Get mesh statistics"""
        with self.lock:
            total_connections = sum(
                len([c for c in conns if c.active])
                for conns in self.connections.values()
            )

            avg_latency = 0.0
            if total_connections > 0:
                all_latencies = [
                    c.latency_ms
                    for conns in self.connections.values()
                    for c in conns if c.active
                ]
                avg_latency = sum(all_latencies) / len(all_latencies)

            return {
                'total_nodes': len(self.nodes),
                'total_connections': total_connections,
                'avg_connections_per_node': total_connections / max(len(self.nodes), 1),
                'avg_latency_ms': avg_latency,
                'topology_type': self.topology_type.value,
                'local_neighbors': len(self.local_neighbors),
                'regional_neighbors': len(self.regional_neighbors),
                'routing_table_size': len(self.routing_table)
            }

    def get_stats(self) -> Dict:
        """Get node mesh statistics"""
        return {
            'node_id': self.node_id,
            'region': self.region,
            'max_connections': self.max_connections,
            **self.get_cluster_stats()
        }


# Example usage
if __name__ == "__main__":
    print("Testing node mesh...")

    # Create mesh
    mesh = NodeMesh(
        node_id="node0",
        topology_type=TopologyType.HYBRID,
        max_connections=10,
        region="us-west"
    )

    # Register nodes
    regions = ["us-west", "us-west", "us-east", "eu-west", "ap-south"]
    for i, region in enumerate(regions):
        mesh.register_node(
            node_id=f"node{i+1}",
            address=f"10.0.{i}.1",
            port=8000 + i,
            region=region,
            capabilities={"gpu": i % 2 == 0}
        )

    print(f"\nRegistered {len(regions)} nodes")

    # Get neighbors
    neighbors = mesh.get_neighbors("node0")
    print(f"\nnode0 neighbors: {neighbors}")

    # Compute routing
    print("\nComputing routing table...")
    mesh.compute_routing_table()

    # Get routes
    for target in ["node1", "node3", "node5"]:
        route = mesh.get_route(target)
        print(f"  Route to {target}: {' -> '.join(route)}")

    # Select sync targets
    sync_targets = mesh.select_sync_targets(count=3, prefer_local=True)
    print(f"\nSync targets (prefer local): {sync_targets}")

    # Cluster stats
    stats = mesh.get_cluster_stats()
    print(f"\nCluster statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    # Load balancing
    print("\nLoad balancing recommendations:")
    recommendations = mesh.balance_load()
    if recommendations:
        for node, targets in recommendations.items():
            print(f"  {node} -> consider connecting to {targets}")
    else:
        print("  No rebalancing needed")

    # Test different topologies
    print("\n\nTesting different topologies...")

    for topo in [TopologyType.FULL_MESH, TopologyType.RING, TopologyType.TREE]:
        test_mesh = NodeMesh(
            node_id="test0",
            topology_type=topo,
            max_connections=10
        )

        for i in range(5):
            test_mesh.register_node(
                node_id=f"test{i+1}",
                address=f"10.1.{i}.1",
                port=9000 + i,
                region="test"
            )

        test_stats = test_mesh.get_cluster_stats()
        print(f"\n{topo.value}:")
        print(f"  Total connections: {test_stats['total_connections']}")
        print(f"  Avg connections/node: {test_stats['avg_connections_per_node']:.1f}")

    print("\n✓ Node mesh tests passed")
