# EchoZero v4.2.1 - Infrastructure Documentation

This directory contains all infrastructure-as-code for deploying EchoZero in various environments.

## Directory Structure

```
infrastructure/
├── README.md                    # This file
├── prometheus.yml               # Prometheus monitoring configuration
├── kubernetes/                  # Raw Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── pvc.yaml
│   ├── rbac.yaml
│   ├── hpa.yaml
│   └── dimensions-configmap.yaml
├── helm/                        # Helm chart
│   └── echozero/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
└── grafana/                     # Grafana dashboards (future)
    ├── dashboards/
    └── datasources/
```

## Prerequisites

### For Docker Compose (Local Development)
- Docker 24.0+
- Docker Compose 2.20+
- NVIDIA Docker runtime (for GPU support)
- 16GB RAM minimum
- NVIDIA GPU with 8GB+ VRAM (recommended)

### For Kubernetes (Production)
- Kubernetes 1.27+
- kubectl configured
- GPU node pool with NVIDIA drivers
- Helm 3.12+ (for Helm deployment)
- Storage provisioner (for PersistentVolumes)

## Deployment Options

### Option 1: Docker Compose (Local Development)

**Quick Start:**
```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f echozero-api

# Access API
curl http://localhost:8000/health

# Access Grafana (admin/echozero)
open http://localhost:3000

# Stop all services
docker-compose down
```

**Services:**
- **echozero-api**: Main API service (port 8000)
- **echozero-autonomy**: Continuous autonomy loop
- **echozero-ui**: Streamlit dashboard (port 8501)
- **prometheus**: Metrics collection (port 9090)
- **grafana**: Visualization dashboards (port 3000)

**GPU Configuration:**
```bash
# CPU-only mode
ECHOZERO_DEVICE=cpu docker-compose up -d

# GPU mode (requires nvidia-docker)
docker-compose up -d
```

---

### Option 2: Kubernetes with Raw Manifests

**Deploy to Kubernetes:**
```bash
# Create namespace
kubectl apply -f infrastructure/kubernetes/namespace.yaml

# Deploy all resources
kubectl apply -f infrastructure/kubernetes/

# Verify deployment
kubectl get pods -n echozero
kubectl get svc -n echozero

# Check logs
kubectl logs -n echozero -l component=api -f

# Port forward for local access
kubectl port-forward -n echozero svc/echozero-api 8000:80
```

**Access API:**
```bash
# Get LoadBalancer IP
kubectl get svc -n echozero echozero-api

# Test health endpoint
curl http://<EXTERNAL-IP>/health
```

**Scaling:**
```bash
# Manual scaling
kubectl scale deployment echozero-api -n echozero --replicas=5

# Autoscaling is configured via HPA
kubectl get hpa -n echozero
```

---

### Option 3: Helm Chart (Recommended for Production)

**Install Chart:**
```bash
# Add local chart repository
helm repo add echozero ./infrastructure/helm

# Install with default values
helm install echozero ./infrastructure/helm/echozero \
  --namespace echozero \
  --create-namespace

# Install with custom values
helm install echozero ./infrastructure/helm/echozero \
  --namespace echozero \
  --create-namespace \
  --values custom-values.yaml
```

**Custom Values Example:**
```yaml
# custom-values.yaml
api:
  replicaCount: 5
  resources:
    requests:
      memory: "8Gi"
      cpu: "4000m"

config:
  N: 128
  rateLimit: 200

persistence:
  checkpoints:
    size: 100Gi

ingress:
  enabled: true
  hosts:
    - host: echozero.example.com
```

**Helm Operations:**
```bash
# Upgrade deployment
helm upgrade echozero ./infrastructure/helm/echozero \
  --namespace echozero \
  --values custom-values.yaml

# Rollback
helm rollback echozero 1 --namespace echozero

# Uninstall
helm uninstall echozero --namespace echozero

# View values
helm get values echozero --namespace echozero
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ECHOZERO_ENV` | `production` | Environment (development/production) |
| `ECHOZERO_LOG_LEVEL` | `INFO` | Logging level |
| `ECHOZERO_N` | `64` | Lattice size |
| `ECHOZERO_DEVICE` | `cuda` | Device (cuda/cpu) |
| `ECHOZERO_RATE_LIMIT` | `100` | API rate limit (requests/window) |
| `ECHOZERO_RATE_WINDOW` | `60` | Rate limit window (seconds) |
| `ECHOZERO_AUTONOMY_DT` | `0.01` | Autonomy loop timestep |
| `ECHOZERO_DRIFT_THRESHOLD` | `0.5` | Drift correction threshold |

### Dimensions Configuration

Edit `config/dimensions.yaml` or ConfigMap to adjust tensor dimensions:
```yaml
N: 64
text_dim: 768
vision_dim: 512
# ... etc
```

---

## Monitoring & Observability

### Prometheus Metrics

**Available Metrics:**
- `echozero_phi_depth` - Current φ-depth value
- `echozero_coherence` - System coherence
- `echozero_drift` - Drift magnitude
- `echozero_requests_total` - Total API requests
- `echozero_request_duration_seconds` - Request latency

**Access Prometheus:**
```bash
# Port forward
kubectl port-forward -n echozero svc/prometheus 9090:9090

# Open browser
open http://localhost:9090
```

### Grafana Dashboards

**Access Grafana:**
```bash
# Port forward
kubectl port-forward -n echozero svc/grafana 3000:3000

# Default credentials: admin/echozero
open http://localhost:3000
```

---

## Storage & Persistence

### Checkpoint Management

**Backup Checkpoints:**
```bash
# Copy from running pod
kubectl cp echozero/<pod-name>:/app/checkpoints ./backup-checkpoints -n echozero

# Restore checkpoints
kubectl cp ./backup-checkpoints echozero/<pod-name>:/app/checkpoints -n echozero
```

**PVC Expansion:**
```bash
# Edit PVC
kubectl edit pvc echozero-checkpoints -n echozero

# Update size in spec.resources.requests.storage
```

---

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -n echozero
kubectl describe pod <pod-name> -n echozero
kubectl logs -n echozero <pod-name> -f
```

### GPU Issues
```bash
# Verify GPU nodes
kubectl get nodes -l accelerator=nvidia-gpu

# Check GPU allocation
kubectl describe node <node-name> | grep nvidia.com/gpu

# Verify NVIDIA plugin
kubectl get daemonset -n kube-system nvidia-device-plugin-daemonset
```

### Common Issues

**Pod stuck in Pending:**
- Check GPU node availability
- Verify PVC binding
- Check resource requests

**OOMKilled:**
- Increase memory limits in values.yaml
- Reduce batch size via ECHOZERO_N

**Health check failures:**
- Check logs for startup errors
- Increase `initialDelaySeconds` in health checks
- Verify PyTorch installation in container

---

## Security Considerations

### Network Policies
```bash
# Enable network policies in Helm
--set networkPolicy.enabled=true
```

### RBAC
- Minimal permissions via ServiceAccount
- Read-only ConfigMap access
- Pod discovery for distributed coordination

### Secrets Management
```bash
# Create secret for API keys (future)
kubectl create secret generic echozero-secrets \
  --from-literal=api-key=<your-key> \
  -n echozero
```

---

## Performance Tuning

### Resource Allocation
```yaml
# High-performance configuration
api:
  replicaCount: 10
  resources:
    requests:
      memory: "16Gi"
      cpu: "8000m"
      nvidia.com/gpu: 2

config:
  N: 128
  rateLimit: 500
```

### Autoscaling Tuning
```yaml
autoscaling:
  minReplicas: 5
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60
```

---

## CI/CD Integration

### Build Image
```bash
docker build -t echozero:v4.2.1 .
docker tag echozero:v4.2.1 registry.example.com/echozero:v4.2.1
docker push registry.example.com/echozero:v4.2.1
```

### GitOps Deployment
```bash
# ArgoCD example
argocd app create echozero \
  --repo https://github.com/your-org/crispy-doodle \
  --path infrastructure/helm/echozero \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace echozero
```

---

## Support & Documentation

- **Main README**: `/README.md`
- **Architecture Review**: `/ARCHITECTURE_REVIEW.md`
- **Implementation Status**: `/IMPLEMENTATION_STATUS.md`
- **API Documentation**: Coming soon

---

**Last Updated**: v4.2.1
**Maintainer**: EchoZero Team
