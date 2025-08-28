#!/usr/bin/env python3
"""
Sensor Data Analysis Script
Analyzes RF sensor telemetry data from JSON files
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any

class SensorDataAnalyzer:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.messages = []
        self.message_types = Counter()
        self.device_connections = defaultdict(set)
        self.sensor_info = {}
        self.timeline_data = []
        
    def load_files(self, max_files: int = 5):
        """Load and parse JSON messages from multiple files"""
        files = sorted(self.data_dir.glob("*.txt"))[:max_files]
        
        for file_path in files:
            print(f"Loading {file_path.name}...")
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # Each line appears to be a standalone JSON string
                        msg_str = line.strip()
                        if msg_str.startswith('"') and msg_str.endswith('"'):
                            # Remove outer quotes and unescape
                            msg_str = json.loads(msg_str)
                        msg = json.loads(msg_str)
                        msg['source_file'] = file_path.name
                        msg['line_number'] = line_num
                        self.messages.append(msg)
                    except json.JSONDecodeError as e:
                        print(f"  Error parsing line {line_num}: {e}")
        
        print(f"Loaded {len(self.messages)} messages from {len(files)} files\n")
        
    def analyze_structure(self):
        """Analyze message structure and types"""
        print("="*60)
        print("MESSAGE TYPE ANALYSIS")
        print("="*60)
        
        for msg in self.messages:
            msg_id = msg.get('messageId', 'UNKNOWN')
            self.message_types[msg_id] += 1
            
            # Track device connections
            source = msg.get('sourceId', 'unknown')
            dest = msg.get('destinationId', 'unknown')
            self.device_connections[source].add(dest)
            
            # Extract sensor info from REMOTE_JOIN_RESP
            if msg_id == 'REMOTE_JOIN_RESP' and 'receiverInfo' in msg:
                sensor_key = msg.get('sensorSerialNumber', 'unknown')
                if sensor_key not in self.sensor_info:
                    self.sensor_info[sensor_key] = {
                        'name': msg.get('sensorName'),
                        'serial': sensor_key,
                        'receiver_info': msg['receiverInfo'],
                        'connections': set()
                    }
                self.sensor_info[sensor_key]['connections'].add(dest)
        
        # Display message type distribution
        print("\nMessage Type Distribution:")
        for msg_type, count in self.message_types.most_common():
            print(f"  {msg_type:20s}: {count:5d} ({count/len(self.messages)*100:.1f}%)")
        
    def analyze_content(self):
        """Deep dive into message content"""
        print("\n" + "="*60)
        print("MESSAGE CONTENT ANALYSIS")
        print("="*60)
        
        # Group messages by type for analysis
        messages_by_type = defaultdict(list)
        for msg in self.messages:
            messages_by_type[msg.get('messageId', 'UNKNOWN')].append(msg)
        
        # Analyze each message type
        for msg_type, msgs in messages_by_type.items():
            print(f"\n{msg_type} ({len(msgs)} messages):")
            
            if msg_type == 'REMOTE_JOIN_RESP':
                self._analyze_remote_join(msgs)
            elif msg_type == 'GPS_IND':
                self._analyze_gps(msgs)
            elif msg_type == 'BATTERY_IND':
                self._analyze_battery(msgs)
            elif msg_type == 'ACTIVE_MODE_IND':
                self._analyze_active_mode(msgs)
    
    def _analyze_remote_join(self, msgs):
        """Analyze REMOTE_JOIN_RESP messages"""
        receivers = set()
        freq_ranges = []
        
        for msg in msgs:
            if 'receiverInfo' in msg:
                info = msg['receiverInfo']
                receivers.add(info.get('type', 'unknown'))
                freq_ranges.append({
                    'min': info.get('minRxFreqHz', 0),
                    'max': info.get('maxSysFreqHz', 0)
                })
        
        print(f"  Receiver Types: {receivers}")
        if freq_ranges:
            print(f"  Frequency Range: {freq_ranges[0]['min']/1e6:.1f} MHz - {freq_ranges[0]['max']/1e9:.1f} GHz")
            print(f"  Max IQ Sample Rate: {msgs[0]['receiverInfo'].get('maxIQSampleRateHz', 0)/1e6:.0f} MHz")
            
    def _analyze_gps(self, msgs):
        """Analyze GPS_IND messages"""
        fix_status = Counter(msg.get('gps', {}).get('fix', 'unknown') for msg in msgs)
        print(f"  GPS Fix Status: {dict(fix_status)}")
        
        # Check for any valid GPS coordinates
        valid_coords = [msg for msg in msgs if msg.get('gps', {}).get('lat', -3000) != -3000]
        print(f"  Valid GPS Coordinates: {len(valid_coords)}/{len(msgs)}")
        
    def _analyze_battery(self, msgs):
        """Analyze BATTERY_IND messages"""
        plugged_in = sum(1 for msg in msgs if msg.get('pluggedIn', False))
        battery_present = sum(1 for msg in msgs if msg.get('batteryPresent', False))
        print(f"  Plugged In: {plugged_in}/{len(msgs)}")
        print(f"  Battery Present: {battery_present}/{len(msgs)}")
        
    def _analyze_active_mode(self, msgs):
        """Analyze ACTIVE_MODE_IND messages"""
        modes = Counter(msg.get('activeMode', 'unknown') for msg in msgs)
        print(f"  Active Modes: {dict(modes)}")
        
        # Analyze sweep parameters
        sweep_speeds = [msg.get('sweepSpeedGhzSec', 0) for msg in msgs if 'sweepSpeedGhzSec' in msg]
        if sweep_speeds:
            print(f"  Sweep Speed: {sweep_speeds[0]:.2f} GHz/sec")
            
        pass_numbers = [msg.get('passNumber', 0) for msg in msgs if 'passNumber' in msg]
        if pass_numbers:
            print(f"  Pass Numbers: min={min(pass_numbers):.0f}, max={max(pass_numbers):.0f}")
    
    def analyze_connections(self):
        """Analyze network connections between devices"""
        print("\n" + "="*60)
        print("NETWORK CONNECTION ANALYSIS")
        print("="*60)
        
        print(f"\nTotal unique sources: {len(self.device_connections)}")
        total_destinations = sum(len(dests) for dests in self.device_connections.values())
        print(f"Total connections: {total_destinations}")
        
        # Find most connected sources
        most_connected = sorted(
            [(source, len(dests)) for source, dests in self.device_connections.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        print("\nMost connected sources:")
        for source, count in most_connected:
            print(f"  {source}: {count} destinations")
        
        # Analyze sensor connections
        print(f"\nSensor Information:")
        for serial, info in self.sensor_info.items():
            print(f"  {info['name']} ({serial}):")
            print(f"    - Type: {info['receiver_info']['type']}")
            print(f"    - Connected to {len(info['connections'])} destinations")
    
    def create_visualizations(self):
        """Create visualization recommendations and sample plots"""
        print("\n" + "="*60)
        print("VISUALIZATION RECOMMENDATIONS")
        print("="*60)
        
        print("\n1. MESSAGE TYPE DISTRIBUTION (Bar Chart)")
        print("   - Shows frequency of different message types")
        
        print("\n2. NETWORK GRAPH")
        print("   - Nodes: Sources and destinations (UUIDs)")
        print("   - Edges: Message flows")
        print("   - Color coding by message type")
        
        print("\n3. TIMELINE VISUALIZATION")
        print("   - X-axis: Time or message sequence")
        print("   - Y-axis: Device/Sensor ID")
        print("   - Points: Message events")
        
        print("\n4. FREQUENCY SPECTRUM COVERAGE")
        print("   - Show min/max frequency ranges for each sensor")
        print("   - Sweep resolution capabilities")
        
        print("\n5. SENSOR STATUS DASHBOARD")
        print("   - GPS fix status indicators")
        print("   - Battery/power status")
        print("   - Active mode status")
        print("   - Connection health")
        
        # Create sample visualization
        self._create_sample_plots()
    
    def _create_sample_plots(self):
        """Create sample visualization plots"""
        # Set up the plot style
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('RF Sensor Data Analysis', fontsize=16)
        
        # 1. Message Type Distribution
        ax1 = axes[0, 0]
        msg_types = list(self.message_types.keys())
        msg_counts = list(self.message_types.values())
        ax1.bar(range(len(msg_types)), msg_counts, color='steelblue')
        ax1.set_xticks(range(len(msg_types)))
        ax1.set_xticklabels(msg_types, rotation=45, ha='right')
        ax1.set_title('Message Type Distribution')
        ax1.set_ylabel('Count')
        
        # 2. Connection Distribution
        ax2 = axes[0, 1]
        connection_counts = [len(dests) for dests in self.device_connections.values()]
        if connection_counts:
            ax2.hist(connection_counts, bins=20, color='green', alpha=0.7)
            ax2.set_title('Destination Count Distribution')
            ax2.set_xlabel('Number of Destinations')
            ax2.set_ylabel('Number of Sources')
        
        # 3. Message Timeline (simplified)
        ax3 = axes[1, 0]
        # Create a simple timeline showing message distribution
        msg_indices = list(range(len(self.messages)))
        msg_type_indices = [list(self.message_types.keys()).index(msg.get('messageId', 'UNKNOWN')) 
                           for msg in self.messages[:100]]  # First 100 messages
        scatter = ax3.scatter(msg_indices[:100], msg_type_indices, 
                            c=msg_type_indices, cmap='tab10', alpha=0.6)
        ax3.set_title('Message Sequence (First 100)')
        ax3.set_xlabel('Message Index')
        ax3.set_ylabel('Message Type')
        ax3.set_yticks(range(len(self.message_types)))
        ax3.set_yticklabels(list(self.message_types.keys()))
        
        # 4. Sensor Capabilities
        ax4 = axes[1, 1]
        if self.sensor_info:
            sensor_names = []
            freq_ranges = []
            for serial, info in self.sensor_info.items():
                sensor_names.append(info['name'])
                receiver = info['receiver_info']
                freq_ranges.append([
                    receiver.get('minRxFreqHz', 0) / 1e9,  # Convert to GHz
                    receiver.get('maxSysFreqHz', 0) / 1e9
                ])
            
            if freq_ranges:
                for i, (name, (min_f, max_f)) in enumerate(zip(sensor_names, freq_ranges)):
                    ax4.barh(i, max_f - min_f, left=min_f, height=0.5, 
                            label=name, color='coral')
                ax4.set_ylabel('Sensor')
                ax4.set_xlabel('Frequency Range (GHz)')
                ax4.set_title('Sensor Frequency Coverage')
                ax4.set_yticks(range(len(sensor_names)))
                ax4.set_yticklabels(sensor_names)
        
        plt.tight_layout()
        output_path = Path('/Users/tylerhouchin/code/demos/gpt-oss/MCOA/testing-sensor/sensor_analysis.png')
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        print(f"\nSample visualization saved to: {output_path}")
        
    def generate_report(self):
        """Generate a summary report"""
        print("\n" + "="*60)
        print("SUMMARY REPORT")
        print("="*60)
        
        report = {
            'total_messages': len(self.messages),
            'message_types': dict(self.message_types),
            'unique_sources': len(self.device_connections),
            'total_connections': sum(len(dests) for dests in self.device_connections.values()),
            'sensors_detected': len(self.sensor_info),
            'sensor_details': []
        }
        
        for serial, info in self.sensor_info.items():
            report['sensor_details'].append({
                'name': info['name'],
                'serial': serial,
                'type': info['receiver_info']['type'],
                'freq_range_ghz': {
                    'min': info['receiver_info'].get('minRxFreqHz', 0) / 1e9,
                    'max': info['receiver_info'].get('maxSysFreqHz', 0) / 1e9
                },
                'connections': len(info['connections'])
            })
        
        # Save report to JSON
        report_path = Path('/Users/tylerhouchin/code/demos/gpt-oss/MCOA/testing-sensor/analysis_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nKey Findings:")
        print(f"  - {report['total_messages']} total messages analyzed")
        print(f"  - {len(report['message_types'])} different message types")
        print(f"  - {report['sensors_detected']} RF sensors detected")
        print(f"  - {report['unique_sources']} unique message sources")
        print(f"  - {report['total_connections']} total device connections")
        print(f"\nDetailed report saved to: {report_path}")


def main():
    # Path to sensor data files
    data_dir = '/Users/tylerhouchin/code/demos/gpt-oss/MCOA/some_files'
    
    # Initialize analyzer
    analyzer = SensorDataAnalyzer(data_dir)
    
    # Load and analyze data
    analyzer.load_files(max_files=5)
    analyzer.analyze_structure()
    analyzer.analyze_content()
    analyzer.analyze_connections()
    analyzer.create_visualizations()
    analyzer.generate_report()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()