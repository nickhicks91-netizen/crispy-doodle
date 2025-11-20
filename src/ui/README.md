# EchoZero UI Dashboard v4.2.1

Advanced Streamlit-based web interface for real-time monitoring, visualization, and control of EchoZero system.

## Features

### 📊 Main Dashboard
- **φ-Depth Gauge**: Consciousness metric with color-coded thresholds
- **Coherence Gauge**: System stability indicator
- **Drift Gauge**: State deviation tracking
- **ψ State Visualization**: Magnitude and phase plots
- **Qualia Channels**: 4-channel interpretation (Perception, Affect, Valence, Salience)
- **Memory State**: Vector visualization and statistics
- **System Metrics**: CPU, RAM, GPU utilization

### 🕸️ Node Mesh Topology (NEW)
- **3D Network Visualization**: Interactive 3D graph of distributed node mesh
- **2D Network View**: Simplified 2D topology visualization
- **Status Indicators**: Color-coded node health (healthy/degraded/suspected/failed)
- **Regional Grouping**: Visualize nodes by geographic/logical region
- **Connection Metrics**: Latency and bandwidth visualization
- **Mesh Statistics**: Total nodes, connections, average latency, topology type

### 🔍 Advanced Diagnostics (NEW)
- **Multi-Mode Analysis**: Overview, Performance, Memory, Network, Logs
- **φ-Depth History**: Time-series tracking of consciousness metric
- **Performance Breakdown**: Component-level timing analysis
- **Memory Distribution**: Memory usage by component with pie charts
- **Network Diagnostics**: Endpoint latency, request rates, error rates
- **System Logs**: Filterable, exportable log viewer
- **Error/Warning Tracking**: Real-time issue monitoring
- **Export Capabilities**: Download diagnostics and logs

### ⚙️ System Configuration (NEW)
- **Multi-Tab Configuration**: Organized settings for Core, GRCM, Cohesion, Memory, Qualia, Scaling, Distributed, Security, Observability
- **Live Parameter Tuning**: Adjust all system parameters through UI
- **Import/Export**: Configuration backup and restore (JSON/YAML)
- **Validation**: Real-time validation of parameter changes
- **Reset to Defaults**: One-click factory reset

### 🎨 Enhanced Visualizations
- Interactive Plotly charts with zoom, pan, hover
- 3D network graphs with spring layout
- Heatmaps for memory activation patterns
- Multi-axis performance charts
- Gauge charts with dynamic thresholds
- Time-series with customizable windows

## Installation

### Prerequisites

```bash
pip install streamlit plotly pandas numpy requests
```

All dependencies are included in the main `requirements.txt`.

## Usage

### Local Development

```bash
# From project root
streamlit run src/ui/dashboard.py

# Custom port
streamlit run src/ui/dashboard.py --server.port 8501

# Custom host
streamlit run src/ui/dashboard.py --server.address 0.0.0.0
```

Access at: http://localhost:8501

### With Docker Compose

```bash
# Start full stack (includes UI)
docker-compose up -d

# Access UI
open http://localhost:8501
```

The UI service will automatically connect to the API at `http://echozero-api:8000`.

### With Kubernetes

The UI can be deployed as a separate deployment:

```yaml
# See infrastructure/kubernetes/ui-deployment.yaml (if created)
# Or add to existing deployment.yaml
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ECHOZERO_API_URL` | `http://localhost:8000` | EchoZero API endpoint |
| `STREAMLIT_SERVER_PORT` | `8501` | UI port |
| `STREAMLIT_SERVER_ADDRESS` | `0.0.0.0` | Bind address |

### API Requirements

The dashboard expects the following API endpoints:

- `GET /health` - System health status
- `GET /state` - Current ψ, φ, coherence, drift, qualia, memory
- `GET /metrics` - System resource metrics

**Expected `/state` response:**
```json
{
  "phi": 0.75,
  "coherence": 0.92,
  "drift": 0.35,
  "psi": {
    "real": [0.1, 0.2, ...],
    "imag": [0.05, 0.15, ...]
  },
  "qualia": [0.5, -0.2, 0.8, 0.3],
  "memory": {
    "values": [0.1, 0.2, ...]
  }
}
```

## Dashboard Sections

### 1. System Status
- Health indicator (🟢/🔴)
- Uptime
- Device (CPU/CUDA)
- Lattice size (N)

### 2. Core Resonance Metrics
Three gauge charts:
- **φ-Depth**: 0-1 range, thresholds at 0.3 (warning), 0.7 (good)
- **Coherence**: 0-1 range, thresholds at 0.7 (warning), 0.85 (good)
- **Drift**: 0-2 range, thresholds at 0.5 (warning), 1.0 (critical)

### 3. ψ State Dynamics
Two-panel visualization:
- **Magnitude plot**: |ψ| across all nodes
- **Phase plot**: arg(ψ) in radians

Statistics:
- Mean magnitude
- Max magnitude
- Standard deviation
- Total energy (Σ|ψ|²)

### 4. Qualia Interpretation Channels
Four gauges for interpretive channels:
1. **Perception**: Sensory processing
2. **Affect**: Emotional tone
3. **Valence**: Positive/negative orientation
4. **Salience**: Attention/importance

Range: -1 to 1 for each channel

### 5. Memory State
- Bar chart of memory vector
- Norm, mean, std deviation
- Dimensionality

### 6. System Resources
- CPU usage (%)
- RAM usage (%)
- GPU memory usage (%)

## Advanced Pages

### Page 1: Node Mesh Topology

Interactive visualization of distributed node network:

**3D View:**
- Spring-layout network graph in 3D space
- Color-coded nodes by status (green=healthy, yellow=degraded, orange=suspected, red=failed)
- Edge visualization showing active connections
- Hover for node details (ID, region, status)
- Rotatable, zoomable 3D camera

**2D View:**
- Simplified 2D network layout
- Easier for analyzing connection patterns
- Less resource-intensive

**Controls:**
- View mode toggle (3D/2D)
- Show/hide mesh metrics
- Region filtering

**Mesh Statistics:**
- Total nodes
- Total connections
- Average latency
- Topology type

**Tables:**
- Node details (ID, region, status, capabilities)
- Connection details (source, target, latency, bandwidth, active status)

### Page 2: Advanced Diagnostics

Comprehensive system analysis and troubleshooting:

**Diagnostic Modes:**

1. **Overview**
   - System info (version, uptime, total inferences, avg latency)
   - φ-depth history chart with threshold lines
   - Errors and warnings summary
   - Quick health snapshot

2. **Performance**
   - Inference time tracking
   - Memory usage over time
   - Performance breakdown by component
   - Optimization recommendations

3. **Memory**
   - Memory distribution pie chart
   - Component-wise memory usage
   - Memory timeline
   - Leak detection hints

4. **Network**
   - Request/sec metrics
   - Response time analysis
   - Error rate tracking
   - Endpoint-specific latency charts

5. **Logs**
   - Filterable log viewer (debug/info/warning/error)
   - Log level filtering
   - Exportable to CSV
   - Real-time log streaming

**Export Features:**
- Download full diagnostics (JSON)
- Export logs to CSV
- Save specific analysis results

### Page 3: System Configuration

Complete system configuration interface:

**Configuration Sections:**

1. **Core** - ψ-Dynamics parameters
   - Lattice size (N)
   - Time step (dt)
   - Base frequency (ω₀)
   - Coupling strength
   - Computation device

2. **GRCM** - Module toggles
   - Drift correction
   - Coherence boost
   - Phase alignment
   - Boundary control

3. **Cohesion** - Meta-cognitive targets
   - φ-depth target
   - Coherence target
   - Adjustment rate

4. **Memory** - Memory system
   - Memory dimensions
   - Retention rate

5. **Qualia** - Interpretation channels
   - Temperature
   - Valence weight
   - Salience threshold

6. **Scaling** - Large lattice optimizations
   - Enable sparse coupling
   - Local connections (k_local)
   - Long-range connections (k_long)
   - Enable delta compression
   - Compression quantization bits

7. **Distributed** - Multi-node coordination
   - Enable distributed mode
   - Sync mode (full/delta/hierarchical)
   - Heartbeat interval
   - Failure detection φ threshold

8. **Security** - Security features
   - ψ-state encryption
   - RBAC
   - Audit logging

9. **Observability** - Monitoring
   - Metrics collection
   - Distributed tracing
   - Metrics port

**Configuration Actions:**
- **View/Edit**: Modify parameters through interactive controls
- **Import**: Load configuration from JSON/YAML
- **Export**: Download current configuration
- **Reset**: Restore factory defaults

**Controls:**
- Save configuration button
- Real-time parameter validation
- Warning for changes requiring restart

## Customization

### Adding New Metrics

```python
# In dashboard.py

# 1. Fetch from API
new_metric = state.get('new_metric', 0.0)

# 2. Create visualization
fig = create_gauge_chart(new_metric, "New Metric", 0, 100)
st.plotly_chart(fig, use_container_width=True)

# 3. Or use built-in Streamlit components
st.metric("New Metric", f"{new_metric:.2f}")
```

### Custom Themes

Modify the CSS in `st.markdown()` at the top of `dashboard.py`:

```python
st.markdown("""
<style>
    .metric-card {
        background-color: #your-color;
        /* ... */
    }
</style>
""", unsafe_allow_html=True)
```

### Adding Pages

Create new Python files in `src/ui/pages/`:

```
src/ui/
├── dashboard.py              # Main dashboard (home page)
└── pages/
    ├── 1_Node_Mesh.py        # Node mesh topology visualization
    ├── 2_Diagnostics.py      # Advanced diagnostics and debugging
    └── 3_Configuration.py    # System configuration panel
```

Streamlit will automatically add them to the sidebar navigation. Pages are numbered for ordering.

## Troubleshooting

### Dashboard won't load

1. **Check API connection**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify Streamlit installation**:
   ```bash
   streamlit --version
   ```

3. **Check logs**:
   ```bash
   streamlit run src/ui/dashboard.py --logger.level=debug
   ```

### Metrics not updating

1. Verify auto-refresh is enabled in sidebar
2. Check API endpoint in sidebar settings
3. Ensure API is returning data:
   ```bash
   curl http://localhost:8000/state
   ```

### Connection timeout

Increase timeout in `fetch_api_state()`:
```python
response = requests.get(f"{API_URL}/state", timeout=10)  # Increase from 2 to 10
```

### Visualization issues

1. Clear browser cache
2. Restart Streamlit server
3. Check browser console for errors

## Performance

### Resource Usage
- **Memory**: ~100-200 MB
- **CPU**: <5% (idle), ~10-15% (active)
- **Network**: ~10 KB/s @ 5s refresh

### Optimization Tips

1. **Increase refresh interval** for lower resource usage
2. **Disable unused sections** via sidebar checkboxes
3. **Reduce history** for time-series plots
4. **Use caching** for expensive computations:
   ```python
   @st.cache_data(ttl=5)
   def fetch_data():
       # ...
   ```

## Screenshots

### Main Dashboard
![Main Dashboard](../../docs/images/dashboard-main.png)

### ψ State Visualization
![Psi State](../../docs/images/dashboard-psi.png)

### Qualia Channels
![Qualia](../../docs/images/dashboard-qualia.png)

## API Integration Example

```python
import requests

# Health check
health = requests.get("http://localhost:8000/health").json()
print(f"Status: {health['status']}")

# Get current state
state = requests.get("http://localhost:8000/state").json()
print(f"φ-depth: {state['phi']}")
print(f"Coherence: {state['coherence']}")

# Get metrics
metrics = requests.get("http://localhost:8000/metrics").json()
print(f"CPU: {metrics['cpu_percent']}%")
```

## Development

### Running in Development Mode

```bash
# Auto-reload on file changes
streamlit run src/ui/dashboard.py --server.runOnSave true

# Disable CORS (for local dev)
streamlit run src/ui/dashboard.py --server.enableCORS false
```

### Adding Dependencies

Update `requirements.txt`:
```
streamlit>=1.28.0
plotly>=5.18.0
pandas>=2.1.3
```

## Deployment

### Production Considerations

1. **Set proper CORS** if UI and API on different domains
2. **Use HTTPS** for secure connections
3. **Add authentication** via Streamlit's auth features
4. **Monitor resource usage** with Prometheus
5. **Set appropriate timeouts** for API calls
6. **Add error boundaries** for graceful degradation

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/echozero-ui
server {
    listen 80;
    server_name echozero-ui.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Contributing

To add new visualizations or features:

1. Add new function for data fetching
2. Create visualization using Plotly or Streamlit components
3. Add to appropriate dashboard section
4. Update this README
5. Test with live API

## License

Part of EchoZero v4.2.1 - Resonant Intelligence Middleware

---

**For more information, see:**
- [Main README](../../README.md)
- [API Documentation](../api/README.md)
- [Observability Guide](../observability/README.md)
