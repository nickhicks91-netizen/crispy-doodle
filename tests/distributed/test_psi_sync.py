"""
Tests for PsiSyncProtocol
"""

import pytest
import torch
from src.distributed.psi_sync import (
    PsiSyncProtocol,
    SyncMode,
    SyncMessage,
    MergeStrategy
)


class TestPsiSyncProtocol:
    """Test suite for ψ-state synchronization"""

    def test_initialization(self):
        """Test protocol initialization"""
        N = 1000
        sync = PsiSyncProtocol(
            node_id="node1",
            N=N,
            mode=SyncMode.DELTA
        )

        assert sync.node_id == "node1"
        assert sync.N == N
        assert sync.mode == SyncMode.DELTA

    def test_propose_state(self):
        """Test proposing local state"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N)

        psi = torch.randn(N, dtype=torch.complex64)
        sync.propose(psi)

        assert sync.local_psi is not None
        assert torch.allclose(sync.local_psi, psi)

    def test_full_sync_message(self):
        """Test FULL sync mode message"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N, mode=SyncMode.FULL)

        psi = torch.randn(N, dtype=torch.complex64)
        sync.propose(psi)

        message = sync.prepare_sync_message()

        assert message.node_id == "node1"
        assert message.mode == SyncMode.FULL
        assert message.psi_data.shape == (N,)
        assert message.checksum is not None

    def test_delta_sync_message(self):
        """Test DELTA sync mode message"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N, mode=SyncMode.DELTA)

        # First state
        psi_0 = torch.randn(N, dtype=torch.complex64)
        sync.propose(psi_0)
        sync.prepare_sync_message()  # Store as previous

        # Second state (small change)
        psi_1 = psi_0 + torch.randn(N, dtype=torch.complex64) * 0.01
        sync.propose(psi_1)

        message = sync.prepare_sync_message()

        assert message.mode == SyncMode.DELTA

        # Delta should be smaller than full state
        delta_magnitude = torch.abs(message.psi_data).mean()
        full_magnitude = torch.abs(psi_1).mean()

        assert delta_magnitude < full_magnitude

    def test_checksum_verification(self):
        """Test checksum verification"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N)

        psi = torch.randn(N, dtype=torch.complex64)
        sync.propose(psi)

        message = sync.prepare_sync_message()

        # Valid checksum
        assert sync._verify_checksum(message.psi_data, message.checksum)

        # Invalid checksum (corrupted data)
        corrupted_data = message.psi_data + 0.001
        assert not sync._verify_checksum(corrupted_data, message.checksum)

    def test_process_sync_message(self):
        """Test processing sync message from remote"""
        N = 100

        # Node 1
        sync1 = PsiSyncProtocol(node_id="node1", N=N, mode=SyncMode.FULL)
        psi1 = torch.randn(N, dtype=torch.complex64)
        sync1.propose(psi1)

        # Node 2
        sync2 = PsiSyncProtocol(node_id="node2", N=N, mode=SyncMode.FULL)
        psi2 = torch.randn(N, dtype=torch.complex64)
        sync2.propose(psi2)

        # Node 2 receives message from Node 1
        message1 = sync1.prepare_sync_message()
        remote_psi = sync2.process_sync_message(message1)

        assert remote_psi is not None
        assert remote_psi.shape == (N,)

        # Should be stored in remote states
        assert "node1" in sync2.remote_states

    def test_merge_average_strategy(self):
        """Test AVERAGE merge strategy"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N, merge_strategy=MergeStrategy.AVERAGE)

        psi1 = torch.ones(N, dtype=torch.complex64)
        psi2 = torch.ones(N, dtype=torch.complex64) * 2

        merged = sync._merge_states(psi1, psi2, MergeStrategy.AVERAGE)

        expected = torch.ones(N, dtype=torch.complex64) * 1.5
        assert torch.allclose(merged, expected)

    def test_merge_latest_strategy(self):
        """Test LATEST merge strategy"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N, merge_strategy=MergeStrategy.LATEST)

        psi1 = torch.ones(N, dtype=torch.complex64)
        psi2 = torch.ones(N, dtype=torch.complex64) * 2

        merged = sync._merge_states(psi1, psi2, MergeStrategy.LATEST)

        # Should take psi2 (remote is "latest")
        assert torch.allclose(merged, psi2)

    def test_merge_weighted_strategy(self):
        """Test WEIGHTED merge strategy"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N, merge_strategy=MergeStrategy.WEIGHTED)

        psi1 = torch.ones(N, dtype=torch.complex64)
        psi2 = torch.ones(N, dtype=torch.complex64) * 2

        # Set weights
        sync.weights["node1"] = 0.7
        sync.weights["node2"] = 0.3

        merged = sync._merge_states(psi1, psi2, MergeStrategy.WEIGHTED, "node2")

        # 0.7 * 1 + 0.3 * 2 = 1.3
        expected = torch.ones(N, dtype=torch.complex64) * 1.3
        assert torch.allclose(merged, expected, atol=1e-5)

    def test_version_tracking(self):
        """Test version tracking"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N)

        psi = torch.randn(N, dtype=torch.complex64)
        sync.propose(psi)

        # Create multiple messages
        msg1 = sync.prepare_sync_message()
        sync.propose(psi + 0.01)
        msg2 = sync.prepare_sync_message()

        # Sequence numbers should increment
        assert msg2.sequence_num > msg1.sequence_num

    def test_conflict_detection(self):
        """Test version conflict detection"""
        N = 100

        sync1 = PsiSyncProtocol(node_id="node1", N=N)
        sync2 = PsiSyncProtocol(node_id="node2", N=N)

        psi = torch.randn(N, dtype=torch.complex64)

        # Both nodes propose
        sync1.propose(psi)
        sync2.propose(psi + 0.1)

        # Exchange messages
        msg1 = sync1.prepare_sync_message()
        msg2 = sync2.prepare_sync_message()

        # Process messages (shouldn't raise errors)
        sync2.process_sync_message(msg1)
        sync1.process_sync_message(msg2)

        # Both should have merged states
        assert sync1.local_psi is not None
        assert sync2.local_psi is not None

    def test_batch_sync(self):
        """Test synchronization with batched states"""
        N = 100
        batch_size = 4

        sync = PsiSyncProtocol(node_id="node1", N=N)

        psi_batch = torch.randn(batch_size, N, dtype=torch.complex64)
        sync.propose(psi_batch[0])  # Only sync first element

        message = sync.prepare_sync_message()

        assert message.psi_data.shape == (N,)

    def test_get_stats(self):
        """Test statistics retrieval"""
        N = 100
        sync = PsiSyncProtocol(node_id="node1", N=N, mode=SyncMode.DELTA)

        stats = sync.get_stats()

        assert stats['node_id'] == "node1"
        assert stats['N'] == N
        assert stats['mode'] == SyncMode.DELTA.value
        assert 'remote_nodes' in stats
        assert 'sequence_num' in stats

    def test_hierarchical_mode(self):
        """Test HIERARCHICAL sync mode"""
        N = 10000
        sync = PsiSyncProtocol(node_id="node1", N=N, mode=SyncMode.HIERARCHICAL)

        psi = torch.randn(N, dtype=torch.complex64)
        sync.propose(psi)

        message = sync.prepare_sync_message()

        assert message.mode == SyncMode.HIERARCHICAL

        # Hierarchical should downsample
        assert message.psi_data.shape[0] < N

    def test_multi_node_convergence(self):
        """Test convergence across multiple nodes"""
        N = 100
        num_nodes = 5

        # Create nodes
        nodes = [
            PsiSyncProtocol(
                node_id=f"node{i}",
                N=N,
                mode=SyncMode.FULL,
                merge_strategy=MergeStrategy.AVERAGE
            )
            for i in range(num_nodes)
        ]

        # Each node proposes different state
        for i, node in enumerate(nodes):
            psi = torch.randn(N, dtype=torch.complex64) + i
            node.propose(psi)

        # Multiple sync rounds
        for round in range(3):
            messages = [node.prepare_sync_message() for node in nodes]

            # Each node processes all other messages
            for i, node in enumerate(nodes):
                for j, message in enumerate(messages):
                    if i != j:
                        node.process_sync_message(message)

        # States should converge
        final_states = [node.local_psi for node in nodes]

        # Check convergence (all states should be similar)
        for i in range(len(final_states) - 1):
            diff = torch.abs(final_states[i] - final_states[i+1]).mean()
            assert diff < 1.0  # Should be reasonably close

    def test_device_handling(self):
        """Test device handling"""
        N = 100

        # CPU
        sync_cpu = PsiSyncProtocol(node_id="node1", N=N, device=torch.device('cpu'))
        psi_cpu = torch.randn(N, dtype=torch.complex64)
        sync_cpu.propose(psi_cpu)

        assert sync_cpu.local_psi.device.type == 'cpu'

        # GPU (if available)
        if torch.cuda.is_available():
            sync_gpu = PsiSyncProtocol(node_id="node2", N=N, device=torch.device('cuda'))
            psi_gpu = torch.randn(N, dtype=torch.complex64, device='cuda')
            sync_gpu.propose(psi_gpu)

            assert sync_gpu.local_psi.device.type == 'cuda'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
