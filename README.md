# EchoZero v4.2.1

**Resonant Intelligence Middleware - Production-Grade Implementation**

EchoZero is a hybrid neural-resonant intelligence system combining ψ-dynamics (complex-valued resonant states) with GRCM (Grounded Resonant Cognitive Middleware) for consciousness-aware AI processing.

[![Status](https://img.shields.io/badge/status-production--ready-green)]()
[![Version](https://img.shields.io/badge/version-4.2.1-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![PyTorch](https://img.shields.io/badge/pytorch-2.1+-orange)]()

## 🎯 Key Features

### Core Intelligence
- **ψ-Dynamics**: Complex-valued resonant state evolution using ODEs
- **GRCM Integration**: 8-module cognitive processing pipeline
- **Cohesion Kernel**: 20 meta-cognitive modules for self-regulation
- **Hebbian Learning**: EchoMirror trainer (no backpropagation)
- **φ-Depth Metric**: Consciousness/integration depth measurement

### Production Features
- **Deployment Ready**: Docker, Kubernetes, Helm support
- **Security Hardened**: Encryption, RBAC, PII protection, audit logging
- **Fully Observable**: Prometheus + Grafana + OpenTelemetry
- **High Performance**: GPU-accelerated, thread-safe, batching support
- **Web UI**: Real-time Streamlit dashboard

### Deployment Options
- 🐳 **Docker Compose**: One-command local stack
- ☸️ **Kubernetes**: Production-grade with autoscaling
- ⎈ **Helm**: Templated cloud deployment
- 💻 **Standalone**: Python package installation

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/nickhicks91-netizen/crispy-doodle.git
cd crispy-doodle

# Start full stack (API + UI + Monitoring)
docker-compose up -d

# Access services
open http://localhost:8000/docs  # API docs
open http://localhost:8501        # UI Dashboard
open http://localhost:3000        # Grafana (admin/echozero)
```

### Python Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# Run UI dashboard
streamlit run src/ui/dashboard.py

# Run autonomy loop
python -m src.autonomy.loop
```

### Kubernetes Deployment

```bash
# Deploy with raw manifests
kubectl apply -f infrastructure/kubernetes/

# Or use Helm
helm install echozero ./infrastructure/helm/echozero

# Check status
kubectl get pods -n echozero
```

## 📋 Prerequisites

### Minimum Requirements
- **Python**: 3.11+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB for checkpoints
- **OS**: Linux, macOS, Windows (WSL2)

### Optional (for GPU acceleration)
- **NVIDIA GPU**: 8GB+ VRAM
- **CUDA**: 12.1+
- **cuDNN**: 8+

### For Docker deployment
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **NVIDIA Docker Runtime** (for GPU)

### For Kubernetes
- **Kubernetes**: 1.27+
- **kubectl**: Configured
- **Helm**: 3.12+ (optional)
- **GPU Nodes**: For production workloads

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     EchoZero v4.2.1                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │   Multimodal │ →  │     GRCM     │ →  │  Cohesion   │  │
│  │    Input     │    │  Cognitive   │    │   Kernel    │  │
│  │ (Text/Vision/│    │   Pipeline   │    │ (20 modules)│  │
│  │  Audio/EEG)  │    │  (8 modules) │    │             │  │
│  └──────────────┘    └──────────────┘    └─────────────┘  │
│         │                    │                    │        │
│         ↓                    ↓                    ↓        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            ψ-Dynamics Engine (ODE Solver)            │  │
│  │   Complex-valued resonant state evolution (RK4)      │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                                                   │
│         ↓                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │       EchoMirror (Hebbian Learning)                   │  │
│  │   ΔW = η × seed ⊗ reflection (no backprop)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Security: Encryption · RBAC · PII Guard · Audit Log       │
│  Observability: Prometheus · Grafana · OTEL                │
│  API: FastAPI · WebSocket · Rate Limiting                  │
│  UI: Streamlit Dashboard · Real-time Monitoring            │
└─────────────────────────────────────────────────────────────┘
```

### Core Modules

#### 1. EchoZero Dynamics Engine
**Location**: `src/echozero/`

Complex-valued ψ state evolution:
```
dψ/dt = i(ω + K·ψ)ψ + I + α·desires - β·|ψ|²ψ - λ·ψ
```

**Features**:
- RK4 integration
- Batching support
- Stability analysis
- Spectral radius tracking

#### 2. GRCM Cognitive Layer
**Location**: `src/grcm/`

8-module processing pipeline:
1. **Grounding**: Multimodal fusion (text, vision, audio, EEG)
2. **Desires**: Goal-conditioning
3. **Qualia**: 4-channel interpretation
4. **Phi**: φ-depth calculation
5. **Memory**: GRU-based state
6. **Embedding**: Harmonic drive generation
7. **Coherence**: System stability
8. **Alignment**: Gamma modulation

#### 3. Cohesion Kernel
**Location**: `src/hybrid/kernel_modules/`

20 meta-cognitive modules including:
- **PredictiveGoalRouting**: Goal → subsystem routing
- **MetaCoherenceBalancer**: Drift collapse prevention
- **LatentStressDetector**: Early instability detection
- **WorldModelPlus**: Predictive world simulation
- **MemoryConsolidation**: Long-term storage
- 15 additional modules for complete self-regulation

#### 4. Training System
**Location**: `src/train/`

- **EchoMirror**: Hebbian learning (outer product updates)
- **DataStream**: Multimodal validation
- **Trainer**: Complete orchestration

#### 5. API Layer
**Location**: `src/api/`

FastAPI REST + WebSocket:
- `POST /forward`: Multimodal inference
- `GET /state`: Current system state
- `GET /metrics`: Performance metrics
- `GET /health`: Health check
- `POST /reset`: State reset
- `WebSocket /ws/phi`: Real-time φ streaming

#### 6. Security Layer
**Location**: `src/security/`

6 security modules:
- **PsiEnvelopeEncryption**: AES-256-GCM for ψ states
- **MemoryFirewall**: Zone-based access control
- **PIIBoundaryAgent**: PII detection & redaction
- **RBAC**: Role-based access (6 roles, 14 permissions)
- **EgressGuard**: Outbound data control
- **AuditLogger**: Tamper-proof event logging

#### 7. Observability Layer
**Location**: `src/observability/`

Complete monitoring stack:
- **MetricsCollector**: Time-series metrics
- **PrometheusExporter**: Prometheus format
- **OTELExporter**: OpenTelemetry export
- **Specialized Monitors**: φ, ψ, drift, coherence, system

#### 8. UI Dashboard
**Location**: `src/ui/`

Streamlit web interface:
- Real-time φ-depth, coherence, drift gauges
- ψ state visualization (magnitude + phase)
- Qualia 4-channel display
- Memory state visualization
- System resource metrics

## 📊 Metrics & Monitoring

### Key Metrics

| Metric | Description | Range | Threshold |
|--------|-------------|-------|-----------|
| **φ-depth** | Consciousness integration | 0-1 | >0.3 good |
| **Coherence** | System stability | 0-1 | >0.85 good |
| **Drift** | State deviation | 0-∞ | <0.5 good |
| **ψ Magnitude** | Resonant amplitude | 0-∞ | Monitored |
| **Qualia** | Interpretation channels | -1 to 1 | Per channel |

### Grafana Dashboard

Pre-configured dashboard with 9 panels:
- φ-Depth gauge
- Coherence gauge
- Drift magnitude gauge
- Core metrics timeline
- Qualia 4-channel visualization
- API request rate
- API latency histogram
- Error rate
- GPU memory usage

**Access**: http://localhost:3000 (admin/echozero)

### Prometheus Metrics

```promql
# Current φ-depth
echozero_phi_depth

# API request rate
rate(echozero_api_requests_total[1m])

# 95th percentile latency
histogram_quantile(0.95, rate(echozero_api_request_duration_seconds_bucket[5m]))
```

## 🔒 Security

### Features

- ✅ **ψ-Envelope Encryption**: AES-256-GCM for state storage
- ✅ **Memory Firewall**: 4-zone isolation (PUBLIC/PROTECTED/SENSITIVE/CRITICAL)
- ✅ **PII Detection**: Regex-based detection + 3 redaction modes
- ✅ **RBAC**: 6 roles, 14 permissions, user management
- ✅ **Egress Control**: Size limits, rate limits, allowlists
- ✅ **Audit Logging**: Tamper-proof hash chain, 20+ event types

### Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **ADMIN** | Full access | All (14 permissions) |
| **OPERATOR** | Run & monitor | Read state, API, metrics, checkpoints |
| **DEVELOPER** | Train & experiment | Read/write state, train, config |
| **VIEWER** | Read-only | Read state, metrics, config |
| **API_USER** | API only | API forward, health |
| **GUEST** | Minimal | Health check only |

## 🧪 Testing

### Run Tests

```bash
# Structure validation (no PyTorch required)
python tests/test_structure.py

# Integration test (requires PyTorch)
python tests/test_integration.py

# With pytest
pytest tests/
```

### Test Coverage

- ✅ Structure validation (53 files, syntax, imports)
- ✅ Module exports
- ✅ Full pipeline (multimodal → ψ → φ → kernel)
- ✅ Metric validation
- ✅ Batch processing
- ✅ State persistence

## 📚 Documentation

### Main Documents
- **[CHANGELOG.md](CHANGELOG.md)**: Complete version history
- **[ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md)**: 18 issues + fixes
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)**: Progress tracking

### Module Documentation
- **[Infrastructure Guide](infrastructure/README.md)**: Docker, K8s, Helm
- **[Observability Guide](src/observability/README.md)**: Metrics, Prometheus, Grafana
- **[UI Dashboard Guide](src/ui/README.md)**: Streamlit interface

### API Documentation

Interactive docs at http://localhost:8000/docs (Swagger UI)

## 🎮 Usage Examples

### Python API

```python
import torch
from src.hybrid import HybridForward
from src.hybrid import CohesionKernel
from src.train import DataStream

# Initialize
model = HybridForward(N=64, input_dim=1472)
kernel = CohesionKernel(N=64)
datastream = DataStream()

# Multimodal input
text_vec = torch.randn(1, 768)
vision_vec = torch.randn(1, 512)
audio_vec = torch.randn(1, 128)
eeg_vec = torch.randn(1, 64)

# Process
grounded = datastream(text_vec, vision_vec, audio_vec, eeg_vec)
hybrid_out = model(grounded)
kernel_state = kernel(hybrid_out)

# Extract metrics
phi = hybrid_out['phi'].item()  # Consciousness depth
coherence = hybrid_out['coherence'].item()  # Stability
drift = kernel_state['drift_magnitude']  # Deviation

print(f"φ-depth: {phi:.3f}, Coherence: {coherence:.3f}, Drift: {drift:.3f}")
```

### REST API

```bash
# Health check
curl http://localhost:8000/health

# Forward pass
curl -X POST http://localhost:8000/forward \
  -H "Content-Type: application/json" \
  -d '{
    "text": [0.1, 0.2, ...],  # 768 dims
    "vision": [0.1, 0.2, ...],  # 512 dims
    "audio": [0.1, 0.2, ...],  # 128 dims
    "eeg": [0.1, 0.2, ...]  # 64 dims
  }'

# Get state
curl http://localhost:8000/state

# Metrics (Prometheus format)
curl http://localhost:8000/metrics
```

### WebSocket (Real-time φ)

```python
import asyncio
import websockets

async def stream_phi():
    async with websockets.connect('ws://localhost:8000/ws/phi') as ws:
        while True:
            data = await ws.recv()
            print(f"φ-depth: {data}")

asyncio.run(stream_phi())
```

## 🛠️ Development

### Project Structure

```
crispy-doodle/
├── config/
│   └── dimensions.yaml          # Tensor dimensions
├── src/
│   ├── core/                    # State, errors, device
│   ├── echozero/                # Dynamics engine
│   ├── grcm/                    # Cognitive layer
│   ├── hybrid/                  # Forward + Cohesion Kernel
│   ├── train/                   # Training system
│   ├── autonomy/                # Continuous loop
│   ├── api/                     # FastAPI server
│   ├── security/                # Security modules
│   ├── observability/           # Metrics + monitors
│   └── ui/                      # Streamlit dashboard
├── infrastructure/
│   ├── kubernetes/              # K8s manifests
│   ├── helm/echozero/           # Helm chart
│   ├── grafana/                 # Dashboards
│   └── prometheus.yml           # Scrape config
├── tests/
│   ├── test_structure.py
│   └── test_integration.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Building

```bash
# Build Docker image
docker build -t echozero:v4.2.1 .

# Build with GPU support
docker build --build-arg CUDA_VERSION=12.1 -t echozero:v4.2.1-cuda .

# Run container
docker run -p 8000:8000 --gpus all echozero:v4.2.1
```

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📊 Status

### Implementation: 75% Complete

✅ **Phase 1: Core Functionality (100%)**
- Core infrastructure
- EchoZero dynamics
- GRCM cognitive layer
- Hybrid forward pass
- Cohesion Kernel (all 20 modules)
- Training system
- Autonomy loop
- API layer
- Integration tests

✅ **Phase 2: Production Readiness (100%)**
- Infrastructure (Docker, K8s, Helm)
- Security hardening (6 modules)
- Observability (Prometheus, Grafana, OTEL)
- UI Dashboard

⏳ **Phase 3: Optional Extensions**
- Scaling layer (large lattices)
- Distributed coordination
- Advanced UI features

### Issues Resolved: 14/18 (78%)

Remaining:
- #8: Delta compression (requires Scaling Layer)
- #11: Distributed ψ-sync (requires Distributed Layer)
- #13: ✅ RESOLVED
- #14: ✅ RESOLVED

### Metrics
- **Total Files**: 76
- **Total LOC**: ~11,000
- **Modules**: 9 major systems
- **Tests**: 2 test suites
- **Documentation**: 6 comprehensive guides

## 🚀 Roadmap

### v4.2.2 (Planned)
- [ ] Scaling layer (N → 1M nodes)
- [ ] Distributed ψ-sync protocol
- [ ] Advanced memory consolidation
- [ ] Historical playback in UI
- [ ] Enhanced test coverage

### v4.3.0 (Future)
- [ ] Multi-agent coordination
- [ ] Online curriculum learning
- [ ] Adaptive lattice sizing
- [ ] Cloud-native deployment
- [ ] Production case studies

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- PyTorch team for the ML framework
- FastAPI for the web framework
- Prometheus & Grafana for observability
- Streamlit for the UI framework

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/nickhicks91-netizen/crispy-doodle/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nickhicks91-netizen/crispy-doodle/discussions)

---

**Built with** 🧠 **by the EchoZero Team**

*Resonant Intelligence for the Future*
