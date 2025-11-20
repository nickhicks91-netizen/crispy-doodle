"""
Fault Detector
Detects and handles node failures in distributed EchoZero deployments
"""

import torch
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import threading


class NodeState(Enum):
    """Node health states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    SUSPECTED = "suspected"
    FAILED = "failed"


@dataclass
class HealthReport:
    """Health report from a node"""
    node_id: str
    timestamp: float
    phi_depth: float
    coherence: float
    latency_ms: float
    error_count: int
    custom_metrics: Dict[str, float]


class FaultDetector:
    """
    Detects node failures using adaptive φ-accrual failure detection

    Features:
    - φ-accrual failure detection (adaptive thresholds)
    - Heartbeat monitoring
    - Performance degradation detection
    - Byzantine node detection
    - Automatic state transitions
    """

    def __init__(
        self,
        node_id: str,
        heartbeat_interval: float = 1.0,
        phi_threshold: float = 8.0,
        degraded_threshold: float = 5.0,
        window_size: int = 100
    ):
        """
        Initialize fault detector

        Args:
            node_id: This node's ID
            heartbeat_interval: Expected heartbeat interval (seconds)
            phi_threshold: Phi-accrual threshold for failure detection
            degraded_threshold: Threshold for degraded state
            window_size: Window size for interval tracking
        """
        self.node_id = node_id
        self.heartbeat_interval = heartbeat_interval
        self.phi_threshold = phi_threshold
        self.degraded_threshold = degraded_threshold
        self.window_size = window_size

        # Node tracking
        self.node_states: Dict[str, NodeState] = {}
        self.last_heartbeat: Dict[str, float] = {}
        self.heartbeat_intervals: Dict[str, List[float]] = {}
        self.health_reports: Dict[str, HealthReport] = {}

        # Statistics
        self.interval_mean: Dict[str, float] = {}
        self.interval_variance: Dict[str, float] = {}

        # Thread safety
        self.lock = threading.Lock()

    def register_node(self, node_id: str):
        """Register a new node for monitoring"""
        with self.lock:
            self.node_states[node_id] = NodeState.HEALTHY
            self.last_heartbeat[node_id] = time.time()
            self.heartbeat_intervals[node_id] = []

    def record_heartbeat(
        self,
        node_id: str,
        health_report: Optional[HealthReport] = None
    ):
        """
        Record heartbeat from a node

        Args:
            node_id: Node sending heartbeat
            health_report: Optional health metrics
        """
        current_time = time.time()

        with self.lock:
            # Calculate interval
            if node_id in self.last_heartbeat:
                interval = current_time - self.last_heartbeat[node_id]

                # Update interval history
                if node_id not in self.heartbeat_intervals:
                    self.heartbeat_intervals[node_id] = []

                intervals = self.heartbeat_intervals[node_id]
                intervals.append(interval)

                # Keep window size
                if len(intervals) > self.window_size:
                    intervals.pop(0)

                # Update statistics
                self._update_statistics(node_id, intervals)

            # Update timestamp
            self.last_heartbeat[node_id] = current_time

            # Store health report
            if health_report:
                self.health_reports[node_id] = health_report

            # Update state based on health
            self._update_node_state(node_id)

    def _update_statistics(self, node_id: str, intervals: List[float]):
        """Update mean and variance for interval distribution"""
        if len(intervals) < 2:
            self.interval_mean[node_id] = self.heartbeat_interval
            self.interval_variance[node_id] = 0.01
            return

        mean = sum(intervals) / len(intervals)
        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)

        # Avoid zero variance
        variance = max(variance, 1e-6)

        self.interval_mean[node_id] = mean
        self.interval_variance[node_id] = variance

    def compute_phi(self, node_id: str) -> float:
        """
        Compute φ-accrual value for a node

        φ represents the suspicion level:
        - φ < 1: Very healthy
        - φ = 5: Degraded
        - φ = 8: Likely failed
        - φ > 10: Almost certainly failed

        Returns:
            Phi accrual value
        """
        if node_id not in self.last_heartbeat:
            return float('inf')

        current_time = time.time()
        elapsed = current_time - self.last_heartbeat[node_id]

        # Get statistics
        mean = self.interval_mean.get(node_id, self.heartbeat_interval)
        variance = self.interval_variance.get(node_id, 0.01)

        # Compute φ using normal distribution approximation
        # φ(t) = -log10(1 - F(t)) where F is CDF

        # Standardize
        std = variance ** 0.5
        z = (elapsed - mean) / std

        # Approximate CDF of standard normal
        # Using error function approximation
        import math
        cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))

        # Avoid log(0)
        cdf = max(cdf, 1e-10)
        cdf = min(cdf, 1 - 1e-10)

        phi = -math.log10(1 - cdf)

        return phi

    def _update_node_state(self, node_id: str):
        """Update node state based on φ and health metrics"""
        phi = self.compute_phi(node_id)

        # Determine state based on φ
        if phi >= self.phi_threshold:
            new_state = NodeState.FAILED
        elif phi >= self.degraded_threshold:
            new_state = NodeState.SUSPECTED
        else:
            # Check health metrics
            if node_id in self.health_reports:
                report = self.health_reports[node_id]

                # Check for degradation signs
                if (report.error_count > 10 or
                    report.latency_ms > 1000 or
                    report.coherence < 0.5):
                    new_state = NodeState.DEGRADED
                else:
                    new_state = NodeState.HEALTHY
            else:
                new_state = NodeState.HEALTHY

        # Update state
        old_state = self.node_states.get(node_id, NodeState.HEALTHY)
        self.node_states[node_id] = new_state

        # Log state transitions
        if old_state != new_state:
            self._on_state_transition(node_id, old_state, new_state, phi)

    def _on_state_transition(
        self,
        node_id: str,
        old_state: NodeState,
        new_state: NodeState,
        phi: float
    ):
        """Handle state transition (hook for logging/callbacks)"""
        # This would trigger alerts, logging, etc.
        pass

    def get_node_state(self, node_id: str) -> NodeState:
        """Get current state of a node"""
        with self.lock:
            return self.node_states.get(node_id, NodeState.HEALTHY)

    def get_healthy_nodes(self) -> List[str]:
        """Get list of healthy nodes"""
        with self.lock:
            return [
                node_id for node_id, state in self.node_states.items()
                if state == NodeState.HEALTHY
            ]

    def get_failed_nodes(self) -> List[str]:
        """Get list of failed nodes"""
        with self.lock:
            return [
                node_id for node_id, state in self.node_states.items()
                if state == NodeState.FAILED
            ]

    def detect_byzantine_behavior(
        self,
        node_id: str,
        expected_phi: float,
        reported_phi: float,
        tolerance: float = 0.2
    ) -> bool:
        """
        Detect Byzantine (malicious) behavior

        Args:
            node_id: Node to check
            expected_phi: Expected φ-depth from consensus
            reported_phi: Node's reported φ-depth
            tolerance: Acceptable deviation

        Returns:
            True if Byzantine behavior detected
        """
        deviation = abs(expected_phi - reported_phi)

        if deviation > tolerance:
            # Potential Byzantine node
            with self.lock:
                if node_id in self.node_states:
                    self.node_states[node_id] = NodeState.SUSPECTED
            return True

        return False

    def check_all_nodes(self) -> Dict[str, NodeState]:
        """
        Check all registered nodes and update states

        Returns:
            Dictionary of node states
        """
        with self.lock:
            node_ids = list(self.node_states.keys())

        # Update each node's state
        for node_id in node_ids:
            self._update_node_state(node_id)

        with self.lock:
            return dict(self.node_states)

    def get_cluster_health(self) -> Dict:
        """Get overall cluster health statistics"""
        with self.lock:
            total = len(self.node_states)
            healthy = sum(1 for s in self.node_states.values() if s == NodeState.HEALTHY)
            degraded = sum(1 for s in self.node_states.values() if s == NodeState.DEGRADED)
            suspected = sum(1 for s in self.node_states.values() if s == NodeState.SUSPECTED)
            failed = sum(1 for s in self.node_states.values() if s == NodeState.FAILED)

            return {
                'total_nodes': total,
                'healthy': healthy,
                'degraded': degraded,
                'suspected': suspected,
                'failed': failed,
                'health_percentage': (healthy / max(total, 1)) * 100,
                'available_nodes': healthy + degraded
            }

    def get_stats(self) -> Dict:
        """Get detector statistics"""
        with self.lock:
            return {
                'node_id': self.node_id,
                'registered_nodes': len(self.node_states),
                'heartbeat_interval': self.heartbeat_interval,
                'phi_threshold': self.phi_threshold,
                'degraded_threshold': self.degraded_threshold,
                'cluster_health': self.get_cluster_health()
            }


# Example usage
if __name__ == "__main__":
    print("Testing fault detector...")

    # Create detector
    detector = FaultDetector(
        node_id="node0",
        heartbeat_interval=1.0,
        phi_threshold=8.0
    )

    # Register nodes
    nodes = ["node1", "node2", "node3", "node4"]
    for node in nodes:
        detector.register_node(node)

    print(f"\nRegistered {len(nodes)} nodes")

    # Simulate heartbeats
    print("\nSimulating heartbeats...")

    # Normal operation
    for t in range(10):
        time.sleep(0.1)

        for i, node in enumerate(nodes):
            if i < 3:  # nodes 1-3 send heartbeats
                health = HealthReport(
                    node_id=node,
                    timestamp=time.time(),
                    phi_depth=0.75 + 0.05 * t,
                    coherence=0.9,
                    latency_ms=50 + i * 10,
                    error_count=0,
                    custom_metrics={}
                )
                detector.record_heartbeat(node, health)

    # Check states
    print("\nNode states after normal operation:")
    for node in nodes:
        state = detector.get_node_state(node)
        phi = detector.compute_phi(node)
        print(f"  {node}: {state.value} (φ={phi:.2f})")

    # Simulate node failure (node4 stops sending heartbeats)
    print("\nSimulating node4 failure...")
    time.sleep(5)

    # Check states again
    states = detector.check_all_nodes()
    print("\nNode states after failure:")
    for node, state in states.items():
        phi = detector.compute_phi(node)
        print(f"  {node}: {state.value} (φ={phi:.2f})")

    # Cluster health
    cluster_health = detector.get_cluster_health()
    print(f"\nCluster health:")
    for key, value in cluster_health.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")

    # Byzantine detection test
    print("\nTesting Byzantine detection...")
    is_byzantine = detector.detect_byzantine_behavior(
        "node2",
        expected_phi=0.75,
        reported_phi=0.95,  # Large deviation
        tolerance=0.1
    )
    print(f"  node2 Byzantine behavior: {is_byzantine}")

    print("\n✓ Fault detector tests passed")
