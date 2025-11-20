"""
Tests for FaultDetector
"""

import pytest
import time
import torch
from src.distributed.fault_detector import (
    FaultDetector,
    NodeState,
    HealthReport
)


class TestFaultDetector:
    """Test suite for fault detection"""

    def test_initialization(self):
        """Test detector initialization"""
        detector = FaultDetector(
            node_id="node0",
            heartbeat_interval=1.0,
            phi_threshold=8.0
        )

        assert detector.node_id == "node0"
        assert detector.phi_threshold == 8.0

    def test_node_registration(self):
        """Test node registration"""
        detector = FaultDetector(node_id="node0")

        detector.register_node("node1")

        assert "node1" in detector.node_states
        assert detector.node_states["node1"] == NodeState.HEALTHY

    def test_heartbeat_recording(self):
        """Test heartbeat recording"""
        detector = FaultDetector(node_id="node0", heartbeat_interval=0.1)

        detector.register_node("node1")

        # Record heartbeats
        for i in range(5):
            detector.record_heartbeat("node1")
            time.sleep(0.05)

        # Should have interval history
        assert len(detector.heartbeat_intervals["node1"]) > 0

    def test_health_report_tracking(self):
        """Test health report tracking"""
        detector = FaultDetector(node_id="node0")

        detector.register_node("node1")

        health = HealthReport(
            node_id="node1",
            timestamp=time.time(),
            phi_depth=0.75,
            coherence=0.9,
            latency_ms=50,
            error_count=0,
            custom_metrics={}
        )

        detector.record_heartbeat("node1", health)

        assert "node1" in detector.health_reports
        assert detector.health_reports["node1"].phi_depth == 0.75

    def test_phi_accrual_computation(self):
        """Test φ-accrual computation"""
        detector = FaultDetector(node_id="node0", heartbeat_interval=0.1)

        detector.register_node("node1")

        # Record regular heartbeats
        for i in range(10):
            detector.record_heartbeat("node1")
            time.sleep(0.05)

        # Phi should be low (healthy)
        phi = detector.compute_phi("node1")
        assert phi < 5.0

    def test_failure_detection(self):
        """Test failure detection"""
        detector = FaultDetector(
            node_id="node0",
            heartbeat_interval=0.1,
            phi_threshold=3.0  # Low threshold for testing
        )

        detector.register_node("node1")

        # Send initial heartbeat
        detector.record_heartbeat("node1")

        # Wait for failure
        time.sleep(1.0)

        # Update state
        detector.check_all_nodes()

        # Should detect failure
        state = detector.get_node_state("node1")
        assert state == NodeState.FAILED

    def test_degradation_detection(self):
        """Test degradation detection"""
        detector = FaultDetector(node_id="node0")

        detector.register_node("node1")

        # Report degraded health
        health = HealthReport(
            node_id="node1",
            timestamp=time.time(),
            phi_depth=0.75,
            coherence=0.3,  # Low coherence
            latency_ms=50,
            error_count=0,
            custom_metrics={}
        )

        detector.record_heartbeat("node1", health)

        state = detector.get_node_state("node1")
        assert state == NodeState.DEGRADED

    def test_byzantine_detection(self):
        """Test Byzantine behavior detection"""
        detector = FaultDetector(node_id="node0")

        detector.register_node("node1")

        # Detect Byzantine behavior
        is_byzantine = detector.detect_byzantine_behavior(
            node_id="node1",
            expected_phi=0.75,
            reported_phi=0.95,  # Large deviation
            tolerance=0.1
        )

        assert is_byzantine
        assert detector.get_node_state("node1") == NodeState.SUSPECTED

    def test_healthy_nodes_list(self):
        """Test getting healthy nodes"""
        detector = FaultDetector(node_id="node0")

        # Register multiple nodes
        for i in range(5):
            detector.register_node(f"node{i}")

        # All should start healthy
        healthy = detector.get_healthy_nodes()
        assert len(healthy) == 5

        # Mark one as failed
        detector.node_states["node2"] = NodeState.FAILED

        healthy = detector.get_healthy_nodes()
        assert len(healthy) == 4
        assert "node2" not in healthy

    def test_failed_nodes_list(self):
        """Test getting failed nodes"""
        detector = FaultDetector(node_id="node0")

        for i in range(5):
            detector.register_node(f"node{i}")

        # Mark some as failed
        detector.node_states["node1"] = NodeState.FAILED
        detector.node_states["node3"] = NodeState.FAILED

        failed = detector.get_failed_nodes()

        assert len(failed) == 2
        assert "node1" in failed
        assert "node3" in failed

    def test_cluster_health(self):
        """Test cluster health statistics"""
        detector = FaultDetector(node_id="node0")

        # Register nodes
        for i in range(10):
            detector.register_node(f"node{i}")

        # Set various states
        detector.node_states["node1"] = NodeState.DEGRADED
        detector.node_states["node2"] = NodeState.SUSPECTED
        detector.node_states["node3"] = NodeState.FAILED
        detector.node_states["node4"] = NodeState.FAILED

        health = detector.get_cluster_health()

        assert health['total_nodes'] == 10
        assert health['healthy'] == 6
        assert health['degraded'] == 1
        assert health['suspected'] == 1
        assert health['failed'] == 2
        assert health['health_percentage'] == 60.0

    def test_statistics_update(self):
        """Test interval statistics update"""
        detector = FaultDetector(node_id="node0", heartbeat_interval=0.1)

        detector.register_node("node1")

        # Record heartbeats with varying intervals
        intervals = [0.09, 0.11, 0.10, 0.12, 0.08]

        for interval in intervals:
            detector.record_heartbeat("node1")
            time.sleep(interval)

        # Should have mean and variance
        assert "node1" in detector.interval_mean
        assert "node1" in detector.interval_variance

        mean = detector.interval_mean["node1"]
        assert 0.05 < mean < 0.15  # Should be around 0.1

    def test_state_transitions(self):
        """Test state transitions"""
        detector = FaultDetector(
            node_id="node0",
            heartbeat_interval=0.1,
            degraded_threshold=2.0,
            phi_threshold=4.0
        )

        detector.register_node("node1")

        # Start healthy
        detector.record_heartbeat("node1")
        assert detector.get_node_state("node1") == NodeState.HEALTHY

        # Transition through states by delaying heartbeats
        # (This is approximate as it depends on timing)

    def test_window_size_limit(self):
        """Test interval window size limit"""
        detector = FaultDetector(
            node_id="node0",
            heartbeat_interval=0.05,
            window_size=10
        )

        detector.register_node("node1")

        # Record many heartbeats
        for i in range(20):
            detector.record_heartbeat("node1")
            time.sleep(0.01)

        # Should only keep window_size intervals
        assert len(detector.heartbeat_intervals["node1"]) <= 10

    def test_multiple_nodes(self):
        """Test tracking multiple nodes"""
        detector = FaultDetector(node_id="node0", heartbeat_interval=0.1)

        num_nodes = 10

        # Register nodes
        for i in range(num_nodes):
            detector.register_node(f"node{i}")

        # Send heartbeats
        for i in range(num_nodes):
            detector.record_heartbeat(f"node{i}")

        # All should be healthy
        assert len(detector.get_healthy_nodes()) == num_nodes

    def test_phi_infinity_for_unknown_node(self):
        """Test φ computation for unknown node"""
        detector = FaultDetector(node_id="node0")

        phi = detector.compute_phi("unknown_node")

        assert phi == float('inf')

    def test_get_stats(self):
        """Test statistics retrieval"""
        detector = FaultDetector(node_id="node0", phi_threshold=8.0)

        for i in range(5):
            detector.register_node(f"node{i}")

        stats = detector.get_stats()

        assert stats['node_id'] == "node0"
        assert stats['registered_nodes'] == 5
        assert stats['phi_threshold'] == 8.0
        assert 'cluster_health' in stats

    def test_concurrent_heartbeats(self):
        """Test concurrent heartbeat recording"""
        detector = FaultDetector(node_id="node0")

        # Register multiple nodes
        for i in range(10):
            detector.register_node(f"node{i}")

        # Concurrent heartbeats (simulated)
        import threading

        def send_heartbeats(node_id, count):
            for _ in range(count):
                detector.record_heartbeat(node_id)
                time.sleep(0.01)

        threads = []
        for i in range(10):
            t = threading.Thread(target=send_heartbeats, args=(f"node{i}", 5))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All nodes should still be tracked
        assert len(detector.node_states) == 10

    def test_error_count_degradation(self):
        """Test degradation based on error count"""
        detector = FaultDetector(node_id="node0")

        detector.register_node("node1")

        # Report high error count
        health = HealthReport(
            node_id="node1",
            timestamp=time.time(),
            phi_depth=0.75,
            coherence=0.9,
            latency_ms=50,
            error_count=15,  # High error count
            custom_metrics={}
        )

        detector.record_heartbeat("node1", health)

        state = detector.get_node_state("node1")
        assert state == NodeState.DEGRADED

    def test_high_latency_degradation(self):
        """Test degradation based on high latency"""
        detector = FaultDetector(node_id="node0")

        detector.register_node("node1")

        # Report high latency
        health = HealthReport(
            node_id="node1",
            timestamp=time.time(),
            phi_depth=0.75,
            coherence=0.9,
            latency_ms=1500,  # High latency
            error_count=0,
            custom_metrics={}
        )

        detector.record_heartbeat("node1", health)

        state = detector.get_node_state("node1")
        assert state == NodeState.DEGRADED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
