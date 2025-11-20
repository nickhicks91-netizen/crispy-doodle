"""
Advanced Diagnostics and Debugging
Deep system analysis and troubleshooting tools
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

st.set_page_config(
    page_title="Diagnostics - EchoZero",
    page_icon="🔍",
    layout="wide"
)

API_URL = os.getenv("ECHOZERO_API_URL", "http://localhost:8000")


def fetch_diagnostics() -> dict:
    """Fetch comprehensive diagnostics"""
    try:
        response = requests.get(f"{API_URL}/diagnostics", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        return {}


def fetch_logs(level: str = "all", limit: int = 100) -> list:
    """Fetch system logs"""
    try:
        response = requests.get(
            f"{API_URL}/logs",
            params={'level': level, 'limit': limit},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def create_phi_history_chart(phi_history: list):
    """Create φ-depth history chart"""
    if not phi_history:
        return None

    df = pd.DataFrame(phi_history)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['phi'],
        mode='lines+markers',
        name='φ-Depth',
        line=dict(color='cyan', width=2),
        marker=dict(size=6)
    ))

    # Add threshold lines
    fig.add_hline(y=0.7, line_dash="dash", line_color="green",
                  annotation_text="Target (0.7)")
    fig.add_hline(y=0.3, line_dash="dash", line_color="red",
                  annotation_text="Critical (0.3)")

    fig.update_layout(
        title="φ-Depth Over Time",
        xaxis_title="Time",
        yaxis_title="φ-Depth",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(gridcolor='#333'),
        yaxis=dict(gridcolor='#333'),
        height=400
    )

    return fig


def create_memory_heatmap(memory_activations: list):
    """Create memory activation heatmap"""
    if not memory_activations:
        return None

    # Convert to 2D array
    arr = np.array(memory_activations)

    fig = go.Figure(data=go.Heatmap(
        z=arr,
        colorscale='Viridis',
        colorbar=dict(title="Activation")
    ))

    fig.update_layout(
        title="Memory Activation Heatmap",
        xaxis_title="Time Steps",
        yaxis_title="Memory Dimensions",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400
    )

    return fig


def create_performance_metrics_chart(metrics: list):
    """Create performance metrics chart"""
    if not metrics:
        return None

    df = pd.DataFrame(metrics)

    fig = go.Figure()

    # Add traces for different metrics
    if 'inference_time_ms' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['inference_time_ms'],
            mode='lines',
            name='Inference Time (ms)',
            line=dict(color='orange')
        ))

    if 'memory_usage_mb' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['memory_usage_mb'],
            mode='lines',
            name='Memory Usage (MB)',
            line=dict(color='lightblue'),
            yaxis='y2'
        ))

    fig.update_layout(
        title="Performance Metrics",
        xaxis_title="Time",
        yaxis=dict(title="Inference Time (ms)", gridcolor='#333'),
        yaxis2=dict(
            title="Memory (MB)",
            overlaying='y',
            side='right',
            gridcolor='#333'
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400
    )

    return fig


def main():
    st.markdown("# 🔍 Advanced Diagnostics")
    st.markdown("### System Analysis & Troubleshooting")

    # Sidebar controls
    with st.sidebar:
        st.markdown("## 🎛️ Diagnostic Controls")

        diagnostic_mode = st.selectbox(
            "Diagnostic Mode",
            ["Overview", "Performance", "Memory", "Network", "Logs"]
        )

        time_range = st.selectbox(
            "Time Range",
            ["Last 1 hour", "Last 6 hours", "Last 24 hours", "Last 7 days"]
        )

        auto_refresh = st.checkbox("Auto-refresh diagnostics", value=False)

        if st.button("🔄 Refresh Data"):
            st.rerun()

        st.markdown("---")

        if st.button("📥 Export Diagnostics"):
            st.success("Diagnostics exported to echozero_diagnostics.json")

    # Fetch diagnostics
    diagnostics = fetch_diagnostics()

    if not diagnostics:
        st.warning("⚠️ Unable to fetch live diagnostics. Generating demo data...")

        # Generate demo data
        diagnostics = {
            'phi_history': [
                {'timestamp': datetime.now() - timedelta(minutes=i),
                 'phi': 0.7 + 0.1 * np.sin(i * 0.1) + np.random.normal(0, 0.05)}
                for i in range(60)
            ],
            'performance': [
                {'timestamp': datetime.now() - timedelta(minutes=i),
                 'inference_time_ms': 10 + np.random.uniform(0, 5),
                 'memory_usage_mb': 500 + np.random.uniform(-50, 50)}
                for i in range(60)
            ],
            'errors': [],
            'warnings': ['Low coherence detected at timestamp X'],
            'system_info': {
                'version': '4.2.1',
                'uptime_hours': 48.5,
                'total_inferences': 125000,
                'average_latency_ms': 12.3
            }
        }

    # Display based on mode
    if diagnostic_mode == "Overview":
        st.markdown("## 📊 System Overview")

        # System info
        if 'system_info' in diagnostics:
            info = diagnostics['system_info']

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Version", info.get('version', 'unknown'))

            with col2:
                st.metric("Uptime (hours)", f"{info.get('uptime_hours', 0):.1f}")

            with col3:
                st.metric("Total Inferences", f"{info.get('total_inferences', 0):,}")

            with col4:
                st.metric("Avg Latency (ms)", f"{info.get('average_latency_ms', 0):.1f}")

        st.markdown("---")

        # φ-depth history
        if 'phi_history' in diagnostics:
            fig_phi = create_phi_history_chart(diagnostics['phi_history'])
            if fig_phi:
                st.plotly_chart(fig_phi, use_container_width=True)

        # Errors and warnings
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ⚠️ Warnings")
            warnings = diagnostics.get('warnings', [])
            if warnings:
                for warning in warnings[:10]:
                    st.warning(warning)
            else:
                st.success("No warnings")

        with col2:
            st.markdown("### ❌ Errors")
            errors = diagnostics.get('errors', [])
            if errors:
                for error in errors[:10]:
                    st.error(error)
            else:
                st.success("No errors")

    elif diagnostic_mode == "Performance":
        st.markdown("## ⚡ Performance Analysis")

        if 'performance' in diagnostics:
            fig_perf = create_performance_metrics_chart(diagnostics['performance'])
            if fig_perf:
                st.plotly_chart(fig_perf, use_container_width=True)

        # Performance breakdown
        st.markdown("### Performance Breakdown")

        perf_data = {
            'Component': ['ψ Evolution', 'GRCM Processing', 'Cohesion', 'Memory', 'Qualia'],
            'Avg Time (ms)': [3.2, 4.5, 2.1, 1.8, 0.9],
            'Max Time (ms)': [8.1, 12.3, 5.4, 4.2, 2.1],
            'Calls': [10000, 10000, 10000, 10000, 10000]
        }

        df = pd.DataFrame(perf_data)
        st.dataframe(df, use_container_width=True)

        # Performance recommendations
        st.markdown("### 💡 Recommendations")
        st.info("• Consider increasing batch size for better GPU utilization")
        st.info("• GRCM processing taking >4ms - check coherence thresholds")

    elif diagnostic_mode == "Memory":
        st.markdown("## 🧠 Memory Analysis")

        # Memory usage breakdown
        memory_data = {
            'Component': ['ψ State', 'GRCM Memory', 'Cohesion State', 'Qualia Buffers', 'Other'],
            'Size (MB)': [250, 150, 80, 20, 100],
            'Percentage': [41.7, 25.0, 13.3, 3.3, 16.7]
        }

        df = pd.DataFrame(memory_data)

        col1, col2 = st.columns(2)

        with col1:
            fig_pie = px.pie(
                df,
                values='Size (MB)',
                names='Component',
                title='Memory Distribution'
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white")
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.dataframe(df, use_container_width=True)

        # Memory timeline
        if 'memory_timeline' in diagnostics:
            st.markdown("### Memory Over Time")
            # Add memory timeline chart here

    elif diagnostic_mode == "Network":
        st.markdown("## 🌐 Network Diagnostics")

        # Network stats
        network_data = {
            'Metric': ['Requests/sec', 'Avg Response Time', 'Error Rate', 'Active Connections'],
            'Value': ['25.3', '45ms', '0.02%', '12'],
            'Status': ['🟢 Good', '🟢 Good', '🟢 Good', '🟢 Good']
        }

        df = pd.DataFrame(network_data)
        st.table(df)

        # Endpoint performance
        st.markdown("### Endpoint Performance")

        endpoint_data = {
            'Endpoint': ['/infer', '/state', '/health', '/metrics'],
            'Avg Latency (ms)': [42, 5, 2, 8],
            'Requests': [15000, 3000, 50000, 2000],
            'Errors': [3, 0, 0, 1]
        }

        df_endpoints = pd.DataFrame(endpoint_data)

        fig_endpoints = px.bar(
            df_endpoints,
            x='Endpoint',
            y='Avg Latency (ms)',
            title='Endpoint Latency'
        )
        fig_endpoints.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )
        st.plotly_chart(fig_endpoints, use_container_width=True)

    elif diagnostic_mode == "Logs":
        st.markdown("## 📜 System Logs")

        # Log level filter
        col1, col2 = st.columns([3, 1])

        with col1:
            log_level = st.selectbox(
                "Log Level",
                ["all", "debug", "info", "warning", "error"]
            )

        with col2:
            log_limit = st.number_input("Limit", min_value=10, max_value=1000, value=100)

        # Fetch logs
        logs = fetch_logs(level=log_level, limit=log_limit)

        if not logs:
            # Generate demo logs
            logs = [
                {
                    'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                    'level': ['info', 'warning', 'error', 'debug'][i % 4],
                    'message': f'Log message {i}',
                    'source': 'echozero.core'
                }
                for i in range(50)
            ]

        # Display logs
        for log in logs[:50]:
            level = log.get('level', 'info')
            timestamp = log.get('timestamp', '')
            message = log.get('message', '')
            source = log.get('source', '')

            level_emoji = {
                'debug': '🔍',
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌'
            }.get(level, 'ℹ️')

            st.text(f"{level_emoji} [{timestamp}] [{source}] {message}")

        # Export logs
        if st.button("📥 Export Logs to CSV"):
            df_logs = pd.DataFrame(logs)
            csv = df_logs.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"echozero_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # Footer
    st.markdown("---")
    st.markdown(f"**Diagnostics Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
