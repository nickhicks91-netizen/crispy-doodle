# EchoZero UI Dashboard

Streamlit-based web interface for real-time monitoring and visualization of EchoZero system.

## Features

### 📊 Real-Time Monitoring
- **φ-Depth Gauge**: Consciousness metric with color-coded thresholds
- **Coherence Gauge**: System stability indicator
- **Drift Gauge**: State deviation tracking
- **ψ State Visualization**: Magnitude and phase plots
- **Qualia Channels**: 4-channel interpretation (Perception, Affect, Valence, Salience)
- **Memory State**: Vector visualization and statistics
- **System Metrics**: CPU, RAM, GPU utilization

### 🎨 Interactive Visualizations
- Gauge charts with thresholds
- Time-series line plots
- Bar charts for memory state
- Phase and magnitude plots for ψ dynamics
- Real-time updates (configurable interval)

### ⚙️ Configuration
- Auto-refresh toggle
- Refresh interval control (1-30 seconds)
- API endpoint configuration
- Display options (show/hide sections)
- Connection status indicator

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
├── dashboard.py          # Main dashboard
└── pages/
    ├── 1_Training.py     # Training metrics
    ├── 2_Logs.py         # System logs
    └── 3_Config.py       # Configuration
```

Streamlit will automatically add them to the sidebar navigation.

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
