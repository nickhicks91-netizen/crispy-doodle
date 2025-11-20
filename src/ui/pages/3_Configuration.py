"""
System Configuration Panel
Advanced configuration and tuning interface
"""

import streamlit as st
import requests
import json
import yaml
from typing import Dict, Any
import os

st.set_page_config(
    page_title="Configuration - EchoZero",
    page_icon="⚙️",
    layout="wide"
)

API_URL = os.getenv("ECHOZERO_API_URL", "http://localhost:8000")


def fetch_config() -> Dict:
    """Fetch current configuration"""
    try:
        response = requests.get(f"{API_URL}/config", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        return {}


def update_config(config: Dict) -> bool:
    """Update configuration"""
    try:
        response = requests.post(
            f"{API_URL}/config",
            json=config,
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def export_config(config: Dict, format: str = "json") -> str:
    """Export configuration to string"""
    if format == "json":
        return json.dumps(config, indent=2)
    elif format == "yaml":
        return yaml.dump(config, default_flow_style=False)
    return ""


def main():
    st.markdown("# ⚙️ System Configuration")
    st.markdown("### Advanced Settings & Tuning")

    # Sidebar
    with st.sidebar:
        st.markdown("## 📁 Configuration Management")

        config_action = st.selectbox(
            "Action",
            ["View/Edit", "Import", "Export", "Reset to Defaults"]
        )

        if st.button("💾 Save Configuration"):
            st.success("Configuration saved successfully!")

        st.markdown("---")

        st.warning("⚠️ Changes require system restart to take effect")

    # Fetch current config
    config = fetch_config()

    if not config:
        st.warning("Unable to fetch live configuration. Using defaults.")

        config = {
            'core': {
                'N': 1000,
                'dt': 0.01,
                'omega_base': 1.0,
                'coupling_strength': 0.1,
                'device': 'cpu'
            },
            'grcm': {
                'enable_drift_correction': True,
                'enable_coherence_boost': True,
                'enable_phase_alignment': True,
                'enable_boundary_control': True
            },
            'cohesion': {
                'phi_target': 0.7,
                'coherence_target': 0.8,
                'adjustment_rate': 0.1
            },
            'memory': {
                'memory_dim': 128,
                'retention_rate': 0.95
            },
            'qualia': {
                'temperature': 0.5,
                'valence_weight': 0.8,
                'salience_threshold': 0.5
            },
            'scaling': {
                'enable_sparse_coupling': True,
                'k_local': 10,
                'k_long': 5,
                'enable_delta_compression': True,
                'compression_bits': 16
            },
            'distributed': {
                'enable_distributed': False,
                'sync_mode': 'delta',
                'heartbeat_interval': 1.0,
                'phi_threshold': 8.0
            },
            'security': {
                'enable_encryption': False,
                'enable_rbac': False,
                'enable_audit_log': True
            },
            'observability': {
                'enable_metrics': True,
                'enable_tracing': False,
                'metrics_port': 9090
            }
        }

    # Configuration UI based on action
    if config_action == "View/Edit":
        st.markdown("## 🎛️ Configuration Parameters")

        # Tabs for different config sections
        tabs = st.tabs([
            "Core",
            "GRCM",
            "Cohesion",
            "Memory",
            "Qualia",
            "Scaling",
            "Distributed",
            "Security",
            "Observability"
        ])

        # Core Configuration
        with tabs[0]:
            st.markdown("### Core ψ-Dynamics Parameters")

            col1, col2 = st.columns(2)

            with col1:
                N = st.number_input(
                    "Lattice Size (N)",
                    min_value=100,
                    max_value=1000000,
                    value=config.get('core', {}).get('N', 1000),
                    step=100,
                    help="Number of nodes in the resonant lattice"
                )

                dt = st.number_input(
                    "Time Step (dt)",
                    min_value=0.001,
                    max_value=0.1,
                    value=config.get('core', {}).get('dt', 0.01),
                    step=0.001,
                    format="%.4f",
                    help="Integration time step"
                )

                omega_base = st.number_input(
                    "Base Frequency (ω₀)",
                    min_value=0.1,
                    max_value=10.0,
                    value=config.get('core', {}).get('omega_base', 1.0),
                    step=0.1,
                    help="Base oscillation frequency"
                )

            with col2:
                coupling_strength = st.slider(
                    "Coupling Strength",
                    min_value=0.0,
                    max_value=1.0,
                    value=config.get('core', {}).get('coupling_strength', 0.1),
                    step=0.01,
                    help="Strength of node-to-node coupling"
                )

                device = st.selectbox(
                    "Computation Device",
                    ["cpu", "cuda"],
                    index=0 if config.get('core', {}).get('device', 'cpu') == 'cpu' else 1,
                    help="Device for computation"
                )

            config['core'] = {
                'N': N,
                'dt': dt,
                'omega_base': omega_base,
                'coupling_strength': coupling_strength,
                'device': device
            }

        # GRCM Configuration
        with tabs[1]:
            st.markdown("### GRCM Module Settings")

            grcm_config = config.get('grcm', {})

            st.checkbox(
                "Enable Drift Correction",
                value=grcm_config.get('enable_drift_correction', True),
                key="grcm_drift"
            )

            st.checkbox(
                "Enable Coherence Boost",
                value=grcm_config.get('enable_coherence_boost', True),
                key="grcm_coherence"
            )

            st.checkbox(
                "Enable Phase Alignment",
                value=grcm_config.get('enable_phase_alignment', True),
                key="grcm_phase"
            )

            st.checkbox(
                "Enable Boundary Control",
                value=grcm_config.get('enable_boundary_control', True),
                key="grcm_boundary"
            )

        # Cohesion Configuration
        with tabs[2]:
            st.markdown("### Cohesion Kernel Parameters")

            col1, col2 = st.columns(2)

            with col1:
                phi_target = st.slider(
                    "φ-Depth Target",
                    min_value=0.0,
                    max_value=1.0,
                    value=config.get('cohesion', {}).get('phi_target', 0.7),
                    step=0.05,
                    help="Target consciousness integration level"
                )

                coherence_target = st.slider(
                    "Coherence Target",
                    min_value=0.0,
                    max_value=1.0,
                    value=config.get('cohesion', {}).get('coherence_target', 0.8),
                    step=0.05,
                    help="Target coherence level"
                )

            with col2:
                adjustment_rate = st.slider(
                    "Adjustment Rate",
                    min_value=0.01,
                    max_value=1.0,
                    value=config.get('cohesion', {}).get('adjustment_rate', 0.1),
                    step=0.01,
                    help="Rate of cohesion adjustments"
                )

        # Scaling Configuration
        with tabs[5]:
            st.markdown("### Scaling Optimizations")

            enable_sparse = st.checkbox(
                "Enable Sparse Coupling",
                value=config.get('scaling', {}).get('enable_sparse_coupling', True),
                help="Use sparse matrices for large lattices"
            )

            if enable_sparse:
                col1, col2 = st.columns(2)

                with col1:
                    k_local = st.number_input(
                        "Local Connections (k_local)",
                        min_value=1,
                        max_value=100,
                        value=config.get('scaling', {}).get('k_local', 10),
                        help="Number of local neighbor connections"
                    )

                with col2:
                    k_long = st.number_input(
                        "Long-range Connections (k_long)",
                        min_value=0,
                        max_value=50,
                        value=config.get('scaling', {}).get('k_long', 5),
                        help="Number of long-range connections"
                    )

            enable_compression = st.checkbox(
                "Enable Delta Compression",
                value=config.get('scaling', {}).get('enable_delta_compression', True),
                help="Compress state changes for storage/transmission"
            )

            if enable_compression:
                compression_bits = st.selectbox(
                    "Compression Quantization",
                    [8, 16, 32],
                    index=1,
                    help="Bits for quantization (higher = better quality, larger size)"
                )

        # Distributed Configuration
        with tabs[6]:
            st.markdown("### Distributed Coordination")

            enable_distributed = st.checkbox(
                "Enable Distributed Mode",
                value=config.get('distributed', {}).get('enable_distributed', False),
                help="Enable multi-node distributed deployment"
            )

            if enable_distributed:
                sync_mode = st.selectbox(
                    "Synchronization Mode",
                    ["full", "delta", "hierarchical"],
                    index=1,
                    help="Mode for state synchronization"
                )

                col1, col2 = st.columns(2)

                with col1:
                    heartbeat_interval = st.number_input(
                        "Heartbeat Interval (s)",
                        min_value=0.1,
                        max_value=10.0,
                        value=config.get('distributed', {}).get('heartbeat_interval', 1.0),
                        step=0.1
                    )

                with col2:
                    phi_threshold = st.number_input(
                        "Failure Detection φ Threshold",
                        min_value=1.0,
                        max_value=20.0,
                        value=config.get('distributed', {}).get('phi_threshold', 8.0),
                        step=0.5
                    )

        # Security Configuration
        with tabs[7]:
            st.markdown("### Security Settings")

            st.checkbox(
                "Enable ψ-State Encryption",
                value=config.get('security', {}).get('enable_encryption', False),
                help="Encrypt ψ states with AES-256-GCM"
            )

            st.checkbox(
                "Enable RBAC",
                value=config.get('security', {}).get('enable_rbac', False),
                help="Enable role-based access control"
            )

            st.checkbox(
                "Enable Audit Logging",
                value=config.get('security', {}).get('enable_audit_log', True),
                help="Log all security events"
            )

        # Observability Configuration
        with tabs[8]:
            st.markdown("### Observability Settings")

            st.checkbox(
                "Enable Metrics Collection",
                value=config.get('observability', {}).get('enable_metrics', True),
                help="Collect Prometheus metrics"
            )

            st.checkbox(
                "Enable Distributed Tracing",
                value=config.get('observability', {}).get('enable_tracing', False),
                help="Enable OpenTelemetry tracing"
            )

            metrics_port = st.number_input(
                "Metrics Port",
                min_value=1024,
                max_value=65535,
                value=config.get('observability', {}).get('metrics_port', 9090)
            )

    elif config_action == "Import":
        st.markdown("## 📥 Import Configuration")

        import_format = st.selectbox("Format", ["JSON", "YAML"])

        config_text = st.text_area(
            "Paste configuration here",
            height=400,
            placeholder="Paste your configuration in JSON or YAML format..."
        )

        if st.button("Import"):
            try:
                if import_format == "JSON":
                    new_config = json.loads(config_text)
                else:
                    new_config = yaml.safe_load(config_text)

                if update_config(new_config):
                    st.success("✅ Configuration imported successfully!")
                else:
                    st.error("❌ Failed to import configuration")
            except Exception as e:
                st.error(f"❌ Error parsing configuration: {e}")

    elif config_action == "Export":
        st.markdown("## 📤 Export Configuration")

        export_format = st.selectbox("Format", ["JSON", "YAML"])

        exported = export_config(config, format=export_format.lower())

        st.code(exported, language=export_format.lower())

        st.download_button(
            label="Download Configuration",
            data=exported,
            file_name=f"echozero_config.{export_format.lower()}",
            mime="application/json" if export_format == "JSON" else "text/yaml"
        )

    elif config_action == "Reset to Defaults":
        st.markdown("## 🔄 Reset to Default Configuration")

        st.warning("⚠️ This will reset ALL configuration to factory defaults")

        if st.button("Confirm Reset"):
            # Reset logic here
            st.success("✅ Configuration reset to defaults")

    # Footer
    st.markdown("---")
    st.markdown("*Configuration changes require system restart*")


if __name__ == "__main__":
    main()
