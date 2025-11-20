"""
EchoZero Dashboard - Streamlit UI
Real-time monitoring and visualization of EchoZero system
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Page configuration
st.set_page_config(
    page_title="EchoZero Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint configuration
API_URL = os.getenv("ECHOZERO_API_URL", "http://localhost:8000")

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .status-good { color: #00ff00; }
    .status-warning { color: #ffaa00; }
    .status-critical { color: #ff0000; }
    .big-number {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
    }
    h1 {
        color: #00d4ff;
    }
    h2 {
        color: #00aaff;
    }
</style>
""", unsafe_allow_html=True)


def fetch_api_state() -> Optional[Dict]:
    """Fetch current state from EchoZero API"""
    try:
        response = requests.get(f"{API_URL}/state", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def fetch_api_metrics() -> Optional[Dict]:
    """Fetch metrics from EchoZero API"""
    try:
        response = requests.get(f"{API_URL}/metrics", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def fetch_api_health() -> Optional[Dict]:
    """Fetch health status from EchoZero API"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def get_status_color(value: float, thresholds: Dict[str, float]) -> str:
    """Get status color based on value and thresholds"""
    if value >= thresholds.get('good', 0.7):
        return 'status-good'
    elif value >= thresholds.get('warning', 0.3):
        return 'status-warning'
    else:
        return 'status-critical'


def create_gauge_chart(value: float, title: str, min_val: float = 0, max_val: float = 1):
    """Create a gauge chart for a metric"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        delta={'reference': 0.5},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickwidth': 1},
            'bar': {'color': "lightblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 0.3], 'color': '#ff4444'},
                {'range': [0.3, 0.7], 'color': '#ffaa00'},
                {'range': [0.7, 1.0], 'color': '#00ff00'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0.9
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': "Arial"},
        height=250
    )

    return fig


def create_time_series_chart(data: List[Dict], title: str, y_label: str):
    """Create a time series line chart"""
    if not data:
        return None

    df = pd.DataFrame(data)

    fig = px.line(
        df,
        x='timestamp',
        y='value',
        title=title,
        labels={'value': y_label, 'timestamp': 'Time'}
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"},
        xaxis={'gridcolor': '#333'},
        yaxis={'gridcolor': '#333'},
        height=300
    )

    return fig


def create_psi_visualization(psi_real: np.ndarray, psi_imag: np.ndarray):
    """Create visualization of ψ state"""
    N = len(psi_real)
    indices = np.arange(N)

    # Magnitude
    magnitude = np.sqrt(psi_real**2 + psi_imag**2)

    # Phase
    phase = np.arctan2(psi_imag, psi_real)

    # Create subplots
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('ψ Magnitude', 'ψ Phase'),
        vertical_spacing=0.15
    )

    # Magnitude plot
    fig.add_trace(
        go.Scatter(
            x=indices,
            y=magnitude,
            mode='lines',
            name='|ψ|',
            line=dict(color='cyan', width=2)
        ),
        row=1, col=1
    )

    # Phase plot
    fig.add_trace(
        go.Scatter(
            x=indices,
            y=phase,
            mode='lines',
            name='arg(ψ)',
            line=dict(color='magenta', width=2)
        ),
        row=2, col=1
    )

    fig.update_xaxes(title_text="Node Index", row=2, col=1)
    fig.update_yaxes(title_text="Magnitude", row=1, col=1)
    fig.update_yaxes(title_text="Phase (rad)", row=2, col=1)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"},
        height=500,
        showlegend=False
    )

    return fig


def main():
    """Main dashboard application"""

    # Title and header
    st.markdown("# 🧠 EchoZero Dashboard v4.2.1")
    st.markdown("### Resonant Intelligence Monitoring System")

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh interval (s)", 1, 30, 5)

        st.markdown("---")
        st.markdown("## 📡 API Configuration")
        api_url_input = st.text_input("API URL", value=API_URL)

        st.markdown("---")
        st.markdown("## 📊 Display Options")
        show_psi_details = st.checkbox("Show ψ state details", value=True)
        show_qualia = st.checkbox("Show qualia channels", value=True)
        show_system_metrics = st.checkbox("Show system metrics", value=True)

        st.markdown("---")
        st.markdown(f"**Status:** {'🟢 Connected' if fetch_api_health() else '🔴 Disconnected'}")

    # Fetch data
    health = fetch_api_health()
    state = fetch_api_state()
    metrics = fetch_api_metrics()

    if not health:
        st.error("⚠️ Unable to connect to EchoZero API")
        st.info(f"Attempting to connect to: {API_URL}")
        st.stop()

    # System Status
    st.markdown("## 🎯 System Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status = health.get('status', 'unknown')
        status_emoji = '🟢' if status == 'healthy' else '🔴'
        st.metric("System Health", f"{status_emoji} {status.upper()}")

    with col2:
        uptime = health.get('uptime_seconds', 0)
        uptime_str = str(timedelta(seconds=int(uptime)))
        st.metric("Uptime", uptime_str)

    with col3:
        device = health.get('device', 'unknown')
        st.metric("Device", device.upper())

    with col4:
        N = health.get('N', 0)
        st.metric("Lattice Size (N)", N)

    st.markdown("---")

    # Core Metrics Gauges
    st.markdown("## 🎨 Core Resonance Metrics")

    if state:
        col1, col2, col3 = st.columns(3)

        with col1:
            phi = state.get('phi', 0.0)
            fig_phi = create_gauge_chart(phi, "φ-Depth (Consciousness)", 0, 1)
            st.plotly_chart(fig_phi, use_container_width=True)

        with col2:
            coherence = state.get('coherence', 0.0)
            fig_coh = create_gauge_chart(coherence, "Coherence (Stability)", 0, 1)
            st.plotly_chart(fig_coh, use_container_width=True)

        with col3:
            drift = state.get('drift', 0.0)
            fig_drift = create_gauge_chart(drift, "Drift Magnitude", 0, 2)
            st.plotly_chart(fig_drift, use_container_width=True)

    st.markdown("---")

    # ψ State Visualization
    if show_psi_details and state and 'psi' in state:
        st.markdown("## 🌊 ψ State Dynamics")

        psi_data = state['psi']
        if isinstance(psi_data, dict):
            psi_real = np.array(psi_data.get('real', []))
            psi_imag = np.array(psi_data.get('imag', []))

            if len(psi_real) > 0:
                fig_psi = create_psi_visualization(psi_real, psi_imag)
                st.plotly_chart(fig_psi, use_container_width=True)

                # ψ statistics
                col1, col2, col3, col4 = st.columns(4)

                magnitude = np.sqrt(psi_real**2 + psi_imag**2)

                with col1:
                    st.metric("ψ Mean Magnitude", f"{magnitude.mean():.4f}")
                with col2:
                    st.metric("ψ Max Magnitude", f"{magnitude.max():.4f}")
                with col3:
                    st.metric("ψ Std Dev", f"{magnitude.std():.4f}")
                with col4:
                    st.metric("ψ Energy", f"{(magnitude**2).sum():.4f}")

        st.markdown("---")

    # Qualia Channels
    if show_qualia and state and 'qualia' in state:
        st.markdown("## 🎭 Qualia Interpretation Channels")

        qualia = state['qualia']
        if isinstance(qualia, list) and len(qualia) == 4:
            col1, col2, col3, col4 = st.columns(4)

            channels = [
                ("Perception", qualia[0], col1),
                ("Affect", qualia[1], col2),
                ("Valence", qualia[2], col3),
                ("Salience", qualia[3], col4)
            ]

            for name, value, col in channels:
                with col:
                    fig = go.Figure(go.Indicator(
                        mode="number+gauge",
                        value=value,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': name, 'font': {'size': 16}},
                        gauge={
                            'axis': {'range': [-1, 1]},
                            'bar': {'color': "lightblue"},
                            'steps': [
                                {'range': [-1, -0.3], 'color': '#ff4444'},
                                {'range': [-0.3, 0.3], 'color': '#ffaa00'},
                                {'range': [0.3, 1], 'color': '#00ff00'}
                            ]
                        }
                    ))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font={'color': "white"},
                        height=200
                    )
                    st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

    # Memory State
    if state and 'memory' in state:
        st.markdown("## 🧩 Memory State")

        memory_data = state['memory']
        if isinstance(memory_data, dict):
            memory_array = np.array(memory_data.get('values', []))

            if len(memory_array) > 0:
                col1, col2 = st.columns(2)

                with col1:
                    fig = go.Figure(data=[go.Bar(
                        x=np.arange(len(memory_array)),
                        y=memory_array,
                        marker_color='lightblue'
                    )])
                    fig.update_layout(
                        title="Memory Vector",
                        xaxis_title="Dimension",
                        yaxis_title="Value",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font={'color': "white"},
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.metric("Memory Norm", f"{np.linalg.norm(memory_array):.4f}")
                    st.metric("Memory Mean", f"{memory_array.mean():.4f}")
                    st.metric("Memory Std", f"{memory_array.std():.4f}")
                    st.metric("Memory Dimensions", len(memory_array))

    st.markdown("---")

    # System Metrics
    if show_system_metrics and metrics:
        st.markdown("## 💻 System Resources")

        col1, col2, col3 = st.columns(3)

        with col1:
            cpu_percent = metrics.get('cpu_percent', 0)
            st.metric("CPU Usage", f"{cpu_percent:.1f}%")

        with col2:
            mem_percent = metrics.get('memory_percent', 0)
            st.metric("RAM Usage", f"{mem_percent:.1f}%")

        with col3:
            gpu_percent = metrics.get('gpu_memory_percent', 0)
            st.metric("GPU Memory", f"{gpu_percent:.1f}%")

    # Footer
    st.markdown("---")
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("*EchoZero v4.2.1 - Resonant Intelligence Middleware*")

    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
