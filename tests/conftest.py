"""
PyTest Configuration
Fixtures and configuration for EchoZero tests
"""

import pytest
import torch
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def device():
    """Get available device (CPU or GPU)"""
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')


@pytest.fixture
def small_N():
    """Small lattice size for quick tests"""
    return 100


@pytest.fixture
def medium_N():
    """Medium lattice size"""
    return 1000


@pytest.fixture
def large_N():
    """Large lattice size"""
    return 10000


@pytest.fixture
def sample_psi(small_N, device):
    """Generate sample ψ state"""
    return torch.randn(small_N, dtype=torch.complex64, device=device) * 0.1


@pytest.fixture
def sample_batch_psi(small_N, device):
    """Generate batch of sample ψ states"""
    batch_size = 4
    return torch.randn(batch_size, small_N, dtype=torch.complex64, device=device) * 0.1


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests that require GPU (deselect with '-m \"not gpu\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks integration tests"
    )
