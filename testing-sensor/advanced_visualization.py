#!/usr/bin/env python3
"""
Advanced Visualization for RF Sensor Data
Creates network graphs and interactive visualizations
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class SensorDataVisualizer:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.messages = []
        self.network_graph = nx.DiGraph()
        
    def load_sample_data(self, max_messages: int = 1000):
        """Load a sample of messages for visualization"""
        files = sorted(self.data_dir.glob("*.txt"))[:2]
        
        for file_path in files:
            with open(file_path, 'r') as f:
                for line in f:
                    if len(self.messages) >= max_messages:
                        break
                    try:
                        msg_str = line.strip()
                        if msg_str.startswith('"') and msg_str.endswith('"'):
                            msg_str = json.loads(msg_str)
                        msg = json.loads(msg_str)
                        self.messages.append(msg)
                    except:
                        pass
        
        print(f"Loaded {len(self.messages)} messages for visualization")
        
    def build_network_graph(self):
        """Build network graph from message flows"""
        message_flows = defaultdict(lambda: defaultdict(int))
        
        for msg in self.messages:
            source = msg.get('sourceId', 'unknown')
            dest = msg.get('destinationId', 'unknown')
            msg_type = msg.get('messageId', 'UNKNOWN')
            
            # Add nodes
            if source not in self.network_graph:
                self.network_graph.add_node(source, node_type='source')
            if dest not in self.network_graph:
                self.network_graph.add_node(dest, node_type='destination')
            
            # Track message flows
            message_flows[(source, dest)][msg_type] += 1
        
        # Add edges with weights
        for (source, dest), msg_types in message_flows.items():
            total_messages = sum(msg_types.values())
            self.network_graph.add_edge(source, dest, 
                                       weight=total_messages,
                                       message_types=dict(msg_types))
    
    def create_interactive_dashboard(self):
        """Create interactive Plotly dashboard"""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Message Type Distribution', 'Message Flow Timeline',
                          'Connection Heatmap', 'Sensor Status Overview'),
            specs=[[{'type': 'bar'}, {'type': 'scatter'}],
                   [{'type': 'heatmap'}, {'type': 'indicator'}]]
        )
        
        # 1. Message Type Distribution
        msg_types = defaultdict(int)
        for msg in self.messages:
            msg_types[msg.get('messageId', 'UNKNOWN')] += 1
        
        fig.add_trace(
            go.Bar(x=list(msg_types.keys()), y=list(msg_types.values()),
                  marker_color='lightblue', name='Message Count'),
            row=1, col=1
        )
        
        # 2. Message Flow Timeline
        timeline_data = []
        for idx, msg in enumerate(self.messages[:500]):  # First 500 messages
            timeline_data.append({
                'index': idx,
                'type': msg.get('messageId', 'UNKNOWN'),
                'destination': msg.get('destinationId', 'unknown')[:8]  # Short UUID
            })
        
        df_timeline = pd.DataFrame(timeline_data)
        type_mapping = {t: i for i, t in enumerate(df_timeline['type'].unique())}
        
        fig.add_trace(
            go.Scatter(
                x=df_timeline['index'],
                y=[type_mapping[t] for t in df_timeline['type']],
                mode='markers',
                marker=dict(
                    color=[type_mapping[t] for t in df_timeline['type']],
                    colorscale='Viridis',
                    size=5
                ),
                text=df_timeline['type'],
                hovertemplate='Message %{x}<br>Type: %{text}<br>Dest: %{customdata}',
                customdata=df_timeline['destination'],
                name='Messages'
            ),
            row=1, col=2
        )
        
        # 3. Connection Heatmap (simplified)
        # Create a small connection matrix
        unique_dests = list(set(msg.get('destinationId', 'unknown') for msg in self.messages))[:10]
        connection_matrix = np.zeros((len(msg_types), len(unique_dests)))
        
        for msg in self.messages:
            msg_type = msg.get('messageId', 'UNKNOWN')
            dest = msg.get('destinationId', 'unknown')
            if msg_type in msg_types and dest in unique_dests:
                type_idx = list(msg_types.keys()).index(msg_type)
                dest_idx = unique_dests.index(dest)
                connection_matrix[type_idx][dest_idx] += 1
        
        fig.add_trace(
            go.Heatmap(
                z=connection_matrix,
                x=[d[:8] for d in unique_dests],  # Short UUIDs
                y=list(msg_types.keys()),
                colorscale='Blues',
                name='Connections'
            ),
            row=2, col=1
        )
        
        # 4. Sensor Status Indicators
        gps_no_fix = sum(1 for msg in self.messages if msg.get('messageId') == 'GPS_IND')
        battery_ok = sum(1 for msg in self.messages if msg.get('messageId') == 'BATTERY_IND' and msg.get('pluggedIn'))
        
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=battery_ok,
                title={'text': "Power Status OK"},
                delta={'reference': len(self.messages)/4, 'relative': True},
                domain={'x': [0, 1], 'y': [0.5, 1]}
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="RF Sensor Network Dashboard",
            showlegend=False,
            height=800
        )
        
        # Save the figure
        output_path = self.data_dir.parent / 'testing-sensor' / 'interactive_dashboard.html'
        fig.write_html(str(output_path))
        print(f"Interactive dashboard saved to: {output_path}")
        
        return fig
    
    def create_network_visualization(self):
        """Create network graph visualization"""
        plt.figure(figsize=(15, 10))
        
        # Build the network
        self.build_network_graph()
        
        # Create layout
        if len(self.network_graph.nodes()) < 100:
            pos = nx.spring_layout(self.network_graph, k=2, iterations=50)
        else:
            # For large graphs, use a simpler layout
            pos = nx.kamada_kawai_layout(self.network_graph)
        
        # Draw nodes
        source_nodes = [n for n, d in self.network_graph.nodes(data=True) if d.get('node_type') == 'source']
        dest_nodes = [n for n, d in self.network_graph.nodes(data=True) if d.get('node_type') == 'destination']
        
        nx.draw_networkx_nodes(self.network_graph, pos, nodelist=source_nodes,
                              node_color='red', node_size=500, label='Source', alpha=0.7)
        nx.draw_networkx_nodes(self.network_graph, pos, nodelist=dest_nodes,
                              node_color='blue', node_size=100, label='Destination', alpha=0.5)
        
        # Draw edges with varying thickness based on message count
        edge_weights = [self.network_graph[u][v]['weight'] for u, v in self.network_graph.edges()]
        max_weight = max(edge_weights) if edge_weights else 1
        edge_widths = [3 * w / max_weight for w in edge_weights]
        
        nx.draw_networkx_edges(self.network_graph, pos, width=edge_widths,
                              alpha=0.3, edge_color='gray', arrows=True)
        
        # Add labels for source nodes only
        source_labels = {n: n[:8] if len(n) > 8 else n for n in source_nodes}
        nx.draw_networkx_labels(self.network_graph, pos, source_labels, font_size=8)
        
        plt.title("RF Sensor Network Communication Graph", fontsize=16)
        plt.legend()
        plt.axis('off')
        plt.tight_layout()
        
        output_path = self.data_dir.parent / 'testing-sensor' / 'network_graph.png'
        plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
        print(f"Network graph saved to: {output_path}")
        
    def create_frequency_spectrum_viz(self):
        """Visualize frequency spectrum coverage"""
        fig = go.Figure()
        
        # Sensor frequency ranges
        sensors = [
            {"name": "P11A-11210037", "min_ghz": 0.03, "max_ghz": 26.5, "type": "CTL26"}
        ]
        
        # Add frequency bands
        common_bands = [
            {"name": "HF", "min": 0.003, "max": 0.03, "color": "lightblue"},
            {"name": "VHF", "min": 0.03, "max": 0.3, "color": "lightgreen"},
            {"name": "UHF", "min": 0.3, "max": 3, "color": "lightyellow"},
            {"name": "L-band", "min": 1, "max": 2, "color": "lightcoral"},
            {"name": "S-band", "min": 2, "max": 4, "color": "lightpink"},
            {"name": "C-band", "min": 4, "max": 8, "color": "lightgray"},
            {"name": "X-band", "min": 8, "max": 12, "color": "lightsalmon"},
            {"name": "Ku-band", "min": 12, "max": 18, "color": "lightsteelblue"},
            {"name": "K-band", "min": 18, "max": 26.5, "color": "lightgoldenrodyellow"}
        ]
        
        # Add background bands
        for band in common_bands:
            fig.add_shape(type="rect",
                         x0=band["min"], x1=band["max"],
                         y0=0, y1=1,
                         fillcolor=band["color"], opacity=0.3,
                         layer="below", line_width=0)
            fig.add_annotation(x=(band["min"] + band["max"])/2, y=0.5,
                             text=band["name"], showarrow=False,
                             font=dict(size=10))
        
        # Add sensor coverage
        for i, sensor in enumerate(sensors):
            fig.add_trace(go.Scatter(
                x=[sensor["min_ghz"], sensor["max_ghz"]],
                y=[i+1.5, i+1.5],
                mode='lines+markers',
                name=f"{sensor['name']} ({sensor['type']})",
                line=dict(width=10, color='red'),
                marker=dict(size=12, symbol='diamond')
            ))
        
        fig.update_layout(
            title="RF Sensor Frequency Coverage",
            xaxis_title="Frequency (GHz)",
            yaxis_title="",
            xaxis_type="log",
            xaxis=dict(range=[np.log10(0.003), np.log10(30)]),
            yaxis=dict(range=[0, 3], showticklabels=False),
            height=400,
            showlegend=True
        )
        
        output_path = self.data_dir.parent / 'testing-sensor' / 'frequency_spectrum.html'
        fig.write_html(str(output_path))
        print(f"Frequency spectrum visualization saved to: {output_path}")


def main():
    data_dir = Path('/Users/tylerhouchin/code/demos/gpt-oss/MCOA/some_files')
    
    visualizer = SensorDataVisualizer(data_dir)
    
    # Load sample data
    visualizer.load_sample_data(max_messages=1000)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    visualizer.create_network_visualization()
    visualizer.create_interactive_dashboard()
    visualizer.create_frequency_spectrum_viz()
    
    print("\n" + "="*60)
    print("VISUALIZATION SUMMARY")
    print("="*60)
    print("\nGenerated Files:")
    print("1. network_graph.png - Network communication graph")
    print("2. interactive_dashboard.html - Interactive Plotly dashboard")
    print("3. frequency_spectrum.html - Frequency coverage visualization")
    print("\nKey Insights:")
    print("- Single sensor (P11A-11210037) broadcasting to multiple destinations")
    print("- Wide frequency coverage: 30 MHz to 26.5 GHz")
    print("- Consistent message pattern: Join->GPS->Battery->Active Mode")
    print("- All messages from WebSocket source ('WS')")
    print("- No GPS fix obtained (all showing NO_FIX)")
    print("- All sensors on external power (no battery)")


if __name__ == '__main__':
    main()