#!/usr/bin/env python3
"""
RF Spectrum Analyzer for Defensive Security Monitoring
Analyzes RF sensor data to detect anomalies and visualize spectrum activity
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import plotly.graph_objs as go
import plotly.offline as pyo
from scipy import signal
from scipy.stats import zscore
import warnings
warnings.filterwarnings('ignore')

class RFSpectrumAnalyzer:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.data = []
        self.df_spectrum = None
        self.anomalies = []
        
    def load_jsonl_data(self, filename='rf_sensor_data.jsonl'):
        """Load JSONL RF sensor data"""
        file_path = self.data_path / filename
        print(f"Loading data from {file_path}")
        
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    self.data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        print(f"Loaded {len(self.data)} records")
        return self.data
    
    def process_spectrum_data(self):
        """Process spectrum data into dataframe"""
        spectrum_records = []
        
        for record in self.data:
            if record.get('messageId') == 'SPECTRUM_DATA':
                timestamp = record['timestamp']
                sweep_num = record.get('sweepNumber', 0)
                
                for spectrum_point in record.get('spectrum', []):
                    spectrum_records.append({
                        'timestamp': timestamp,
                        'sweep_number': sweep_num,
                        'freq_mhz': spectrum_point['freq_mhz'],
                        'power_dbm': spectrum_point['power_dbm'],
                        'bandwidth_khz': spectrum_point['bandwidth_khz']
                    })
        
        self.df_spectrum = pd.DataFrame(spectrum_records)
        self.df_spectrum['timestamp'] = pd.to_datetime(self.df_spectrum['timestamp'])
        return self.df_spectrum
    
    def detect_anomalies(self, threshold=2.5):
        """Detect anomalous RF signals using statistical methods"""
        if self.df_spectrum is None:
            self.process_spectrum_data()
        
        # Group by frequency and calculate statistics
        freq_stats = self.df_spectrum.groupby('freq_mhz')['power_dbm'].agg(['mean', 'std'])
        
        # Detect anomalies (signals significantly above noise floor)
        anomalies = []
        for _, row in self.df_spectrum.iterrows():
            freq = row['freq_mhz']
            power = row['power_dbm']
            
            if freq in freq_stats.index:
                mean_power = freq_stats.loc[freq, 'mean']
                std_power = freq_stats.loc[freq, 'std']
                
                # Higher power than expected (less negative)
                if std_power > 0 and power > mean_power + threshold * std_power:
                    anomalies.append({
                        'timestamp': row['timestamp'],
                        'freq_mhz': freq,
                        'power_dbm': power,
                        'expected_power': mean_power,
                        'deviation': (power - mean_power) / std_power
                    })
        
        self.anomalies = pd.DataFrame(anomalies)
        return self.anomalies
    
    def plot_waterfall(self, save_path=None):
        """Create waterfall plot of RF spectrum over time"""
        if self.df_spectrum is None:
            self.process_spectrum_data()
        
        # Pivot data for heatmap
        pivot_data = self.df_spectrum.pivot_table(
            values='power_dbm',
            index='sweep_number',
            columns='freq_mhz',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(15, 8))
        sns.heatmap(pivot_data, cmap='viridis', cbar_kws={'label': 'Power (dBm)'})
        plt.title('RF Spectrum Waterfall Plot')
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Time (Sweep Number)')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_frequency_bands(self, save_path=None):
        """Analyze and visualize different frequency bands"""
        if self.df_spectrum is None:
            self.process_spectrum_data()
        
        # Define common RF bands
        bands = {
            '433 MHz ISM': (432, 434),
            '900 MHz ISM': (902, 928),
            'GPS L1': (1574, 1577),
            '2.4 GHz WiFi/BT': (2400, 2480),
            '5 GHz WiFi Lower': (5170, 5250),
            '5 GHz WiFi Upper': (5735, 5835)
        }
        
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for idx, (band_name, (freq_min, freq_max)) in enumerate(bands.items()):
            ax = axes[idx]
            
            # Filter data for this band
            band_data = self.df_spectrum[
                (self.df_spectrum['freq_mhz'] >= freq_min) & 
                (self.df_spectrum['freq_mhz'] <= freq_max)
            ]
            
            if not band_data.empty:
                # Average power across all sweeps
                avg_power = band_data.groupby('freq_mhz')['power_dbm'].mean()
                max_power = band_data.groupby('freq_mhz')['power_dbm'].max()
                
                ax.plot(avg_power.index, avg_power.values, 'b-', label='Average', alpha=0.7)
                ax.plot(max_power.index, max_power.values, 'r-', label='Peak', alpha=0.5)
                ax.fill_between(avg_power.index, -130, avg_power.values, alpha=0.3)
                
                ax.set_title(f'{band_name} Band')
                ax.set_xlabel('Frequency (MHz)')
                ax.set_ylabel('Power (dBm)')
                ax.grid(True, alpha=0.3)
                ax.legend()
                ax.set_ylim([-130, -50])
        
        plt.suptitle('RF Spectrum Analysis by Frequency Band', fontsize=16)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_interactive_plot(self, output_file='rf_spectrum_interactive.html'):
        """Create interactive Plotly visualization"""
        if self.df_spectrum is None:
            self.process_spectrum_data()
        
        # Get unique sweep numbers
        sweeps = sorted(self.df_spectrum['sweep_number'].unique())
        
        # Create traces for each sweep
        traces = []
        for sweep in sweeps[:20]:  # Limit to first 20 sweeps for clarity
            sweep_data = self.df_spectrum[self.df_spectrum['sweep_number'] == sweep]
            trace = go.Scatter(
                x=sweep_data['freq_mhz'],
                y=sweep_data['power_dbm'],
                mode='lines',
                name=f'Sweep {sweep}',
                opacity=0.7
            )
            traces.append(trace)
        
        # Create layout
        layout = go.Layout(
            title='Interactive RF Spectrum Analysis',
            xaxis=dict(title='Frequency (MHz)'),
            yaxis=dict(title='Power (dBm)'),
            hovermode='closest',
            showlegend=True
        )
        
        fig = go.Figure(data=traces, layout=layout)
        
        # Save to HTML
        output_path = self.data_path / output_file
        pyo.plot(fig, filename=str(output_path), auto_open=False)
        print(f"Interactive plot saved to {output_path}")
    
    def analyze_signal_activity(self):
        """Analyze signal activity patterns"""
        if self.df_spectrum is None:
            self.process_spectrum_data()
        
        # Find active frequencies (signals above noise floor)
        noise_floor = -115  # dBm typical noise floor
        active_signals = self.df_spectrum[self.df_spectrum['power_dbm'] > noise_floor]
        
        # Group by frequency to find persistent signals
        freq_activity = active_signals.groupby('freq_mhz').agg({
            'power_dbm': ['mean', 'max', 'count'],
            'timestamp': ['min', 'max']
        })
        
        freq_activity.columns = ['avg_power', 'max_power', 'occurrences', 'first_seen', 'last_seen']
        freq_activity = freq_activity.sort_values('occurrences', ascending=False)
        
        print("\n=== Top Active Frequencies ===")
        print(freq_activity.head(20))
        
        # Identify frequency bands with activity
        band_activity = {
            '433 MHz': active_signals[(active_signals['freq_mhz'] >= 432) & (active_signals['freq_mhz'] <= 434)].shape[0],
            '900 MHz': active_signals[(active_signals['freq_mhz'] >= 902) & (active_signals['freq_mhz'] <= 928)].shape[0],
            'GPS': active_signals[(active_signals['freq_mhz'] >= 1574) & (active_signals['freq_mhz'] <= 1577)].shape[0],
            '2.4 GHz': active_signals[(active_signals['freq_mhz'] >= 2400) & (active_signals['freq_mhz'] <= 2480)].shape[0],
            '5 GHz Lower': active_signals[(active_signals['freq_mhz'] >= 5170) & (active_signals['freq_mhz'] <= 5250)].shape[0],
            '5 GHz Upper': active_signals[(active_signals['freq_mhz'] >= 5735) & (active_signals['freq_mhz'] <= 5835)].shape[0]
        }
        
        print("\n=== Band Activity Summary ===")
        for band, count in band_activity.items():
            print(f"{band}: {count} active measurements")
        
        return freq_activity, band_activity
    
    def generate_report(self, output_file='rf_analysis_report.txt'):
        """Generate comprehensive analysis report"""
        report_path = self.data_path / output_file
        
        with open(report_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("RF SPECTRUM ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            
            # Data summary
            f.write("DATA SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total records: {len(self.data)}\n")
            
            if self.df_spectrum is not None:
                f.write(f"Total spectrum measurements: {len(self.df_spectrum)}\n")
                f.write(f"Unique frequencies monitored: {self.df_spectrum['freq_mhz'].nunique()}\n")
                f.write(f"Time range: {self.df_spectrum['timestamp'].min()} to {self.df_spectrum['timestamp'].max()}\n")
                f.write(f"Number of sweeps: {self.df_spectrum['sweep_number'].nunique()}\n\n")
            
            # Anomaly detection results
            if not self.anomalies.empty:
                f.write("DETECTED ANOMALIES\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total anomalies detected: {len(self.anomalies)}\n")
                f.write("\nTop anomalous frequencies:\n")
                top_anomalies = self.anomalies.groupby('freq_mhz').size().sort_values(ascending=False).head(10)
                for freq, count in top_anomalies.items():
                    f.write(f"  {freq:.2f} MHz: {count} occurrences\n")
            
            # Signal activity analysis
            freq_activity, band_activity = self.analyze_signal_activity()
            
            f.write("\n\nBAND ACTIVITY ANALYSIS\n")
            f.write("-" * 40 + "\n")
            for band, count in band_activity.items():
                f.write(f"{band:15s}: {count:6d} active measurements\n")
            
            f.write("\n\nMOST ACTIVE FREQUENCIES\n")
            f.write("-" * 40 + "\n")
            f.write(freq_activity.head(20).to_string())
            
        print(f"\nReport saved to {report_path}")
        return report_path


def main():
    # Initialize analyzer
    analyzer = RFSpectrumAnalyzer(Path('/Users/tylerhouchin/code/demos/gpt-oss/MCOA/testing-sensor'))
    
    # Load data
    analyzer.load_jsonl_data()
    
    # Process spectrum data
    analyzer.process_spectrum_data()
    
    # Detect anomalies
    anomalies = analyzer.detect_anomalies()
    if not anomalies.empty:
        print(f"\nDetected {len(anomalies)} anomalous signals")
        print("\nTop anomalous frequencies:")
        print(anomalies.groupby('freq_mhz').size().sort_values(ascending=False).head(10))
    
    # Create visualizations
    print("\nGenerating visualizations...")
    analyzer.plot_waterfall(save_path='rf_waterfall.png')
    analyzer.plot_frequency_bands(save_path='rf_bands_analysis.png')
    analyzer.create_interactive_plot()
    
    # Generate report
    analyzer.generate_report()
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()