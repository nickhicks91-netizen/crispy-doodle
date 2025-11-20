"""
Node Mesh Topology Visualization
Advanced visualization of distributed node mesh
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import networkx as nx
import numpy as np
from typing import Dict, List, Optional
import os

st.set_page_config(
    page_title="Node Mesh - EchoZero",
    page_icon="🕸️",
    layout="wide"
)

API_URL = os.getenv("ECHOZERO_API_URL", "http://localhost:8000")


def fetch_mesh_topology() -> Optional[Dict]:
    """Fetch mesh topology from API"""
    try:
        response = requests.get(f"{API_URL}/mesh/topology", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def create_mesh_graph(nodes: List[Dict], connections: List[Dict]):
    """Create 3D network graph of mesh topology"""

    # Create NetworkX graph
    G = nx.Graph()

    # Add nodes
    for node in nodes:
        G.add_node(
            node['node_id'],
            region=node.get('region', 'unknown'),
            status=node.get('status', 'unknown')
        )

    # Add edges
    for conn in connections:
        if conn['active']:
            G.add_edge(
                conn['source'],
                conn['target'],
                weight=conn.get('latency_ms', 10)
            )

    # Use spring layout for 3D positions
    pos_2d = nx.spring_layout(G, seed=42)

    # Convert to 3D (add random z)
    pos = {}
    for node_id, (x, y) in pos_2d.items():
        z = np.random.uniform(-0.5, 0.5)
        pos[node_id] = (x, y, z)

    # Create edge trace
    edge_x = []
    edge_y = []
    edge_z = []

    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=dict(color='#888', width=2),
        hoverinfo='none',
        name='Connections'
    )

    # Create node trace
    node_x = []
    node_y = []
    node_z = []
    node_text = []
    node_colors = []

    status_colors = {
        'healthy': 'green',
        'degraded': 'yellow',
        'suspected': 'orange',
        'failed': 'red',
        'unknown': 'gray'
    }

    for node_id in G.nodes():
        x, y, z = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)

        node_data = G.nodes[node_id]
        status = node_data.get('status', 'unknown')
        region = node_data.get('region', 'unknown')

        node_text.append(f"{node_id}<br>Region: {region}<br>Status: {status}")
        node_colors.append(status_colors.get(status, 'gray'))

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        marker=dict(
            size=15,
            color=node_colors,
            line=dict(color='white', width=2)
        ),
        text=[node_id for node_id in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        hoverinfo='text',
        name='Nodes'
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])

    fig.update_layout(
        title="Node Mesh Topology (3D)",
        showlegend=True,
        scene=dict(
            xaxis=dict(showgrid=False, showbackground=False, showticklabels=False),
            yaxis=dict(showgrid=False, showbackground=False, showticklabels=False),
            zaxis=dict(showgrid=False, showbackground=False, showticklabels=False),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=700
    )

    return fig


def create_2d_mesh_graph(nodes: List[Dict], connections: List[Dict]):
    """Create 2D network graph"""

    G = nx.Graph()

    for node in nodes:
        G.add_node(node['node_id'])

    for conn in connections:
        if conn['active']:
            G.add_edge(conn['source'], conn['target'])

    pos = nx.spring_layout(G, seed=42)

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(color='#888', width=2),
        hoverinfo='none'
    )

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(size=20, color='lightblue', line=dict(color='white', width=2)),
        text=[node for node in G.nodes()],
        textposition="top center",
        hoverinfo='text'
    )

    fig = go.Figure(data=[edge_trace, node_trace])

    fig.update_layout(
        title="Node Mesh Topology (2D)",
        showlegend=False,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=600
    )

    return fig


def main():
    st.markdown("# 🕸️ Node Mesh Topology")
    st.markdown("### Distributed Network Visualization")

    # Sidebar controls
    with st.sidebar:
        st.markdown("## 📊 Visualization Settings")

        view_mode = st.radio("View Mode", ["3D", "2D"])
        show_metrics = st.checkbox("Show Mesh Metrics", value=True)
        highlight_region = st.selectbox(
            "Highlight Region",
            ["All", "us-west", "us-east", "eu-west", "ap-south"]
        )

    # Fetch topology
    topology = fetch_mesh_topology()

    if not topology:
        # Generate demo data for visualization
        st.warning("Unable to fetch live topology. Showing demo data.")

        nodes = [
            {'node_id': f'node{i}', 'region': ['us-west', 'us-east', 'eu-west'][i % 3],
             'status': 'healthy'}
            for i in range(12)
        ]

        connections = []
        for i in range(len(nodes)):
            for j in range(i+1, min(i+4, len(nodes))):
                connections.append({
                    'source': nodes[i]['node_id'],
                    'target': nodes[j]['node_id'],
                    'active': True,
                    'latency_ms': np.random.uniform(10, 100)
                })

        topology = {
            'nodes': nodes,
            'connections': connections,
            'stats': {
                'total_nodes': len(nodes),
                'total_connections': len(connections),
                'avg_latency_ms': 50.0,
                'topology_type': 'hybrid'
            }
        }

    # Display graph
    if view_mode == "3D":
        fig = create_mesh_graph(topology['nodes'], topology['connections'])
    else:
        fig = create_2d_mesh_graph(topology['nodes'], topology['connections'])

    st.plotly_chart(fig, use_container_width=True)

    # Mesh statistics
    if show_metrics and 'stats' in topology:
        st.markdown("## 📈 Mesh Statistics")

        stats = topology['stats']

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Nodes", stats.get('total_nodes', 0))

        with col2:
            st.metric("Total Connections", stats.get('total_connections', 0))

        with col3:
            st.metric("Avg Latency (ms)", f"{stats.get('avg_latency_ms', 0):.1f}")

        with col4:
            st.metric("Topology Type", stats.get('topology_type', 'unknown').upper())

    # Node details table
    st.markdown("## 📋 Node Details")

    import pandas as pd

    nodes_df = pd.DataFrame(topology['nodes'])
    st.dataframe(nodes_df, use_container_width=True)

    # Connection details
    with st.expander("🔗 Connection Details"):
        conn_df = pd.DataFrame(topology['connections'])
        st.dataframe(conn_df, use_container_width=True)


if __name__ == "__main__":
    main()
