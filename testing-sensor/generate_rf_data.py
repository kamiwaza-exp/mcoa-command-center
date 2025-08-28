#!/usr/bin/env python3
"""
Generate simulated RF sensor data with actual spectrum measurements
Including drone signatures at specific times
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
import math

class RFDataSimulator:
    def __init__(self):
        self.base_noise_floor = -120  # dBm
        self.sensor_info = {
            "type": "CTL26",
            "serial": "P11A-11210037",
            "name": "Local Sensor View"
        }
        
        # Common frequency bands to monitor (in MHz)
        self.frequency_bands = [
            # ISM Bands
            {"freq": 433.0, "name": "ISM_433", "bandwidth": 1.0},
            {"freq": 915.0, "name": "ISM_915", "bandwidth": 26.0},
            
            # GPS
            {"freq": 1575.42, "name": "GPS_L1", "bandwidth": 2.0},
            
            # WiFi/Drone Control
            {"freq": 2412.0, "name": "WiFi_Ch1", "bandwidth": 20.0},
            {"freq": 2437.0, "name": "WiFi_Ch6", "bandwidth": 20.0},
            {"freq": 2462.0, "name": "WiFi_Ch11", "bandwidth": 20.0},
            
            # 5GHz Band
            {"freq": 5180.0, "name": "5G_Ch36", "bandwidth": 20.0},
            {"freq": 5745.0, "name": "5G_Ch149", "bandwidth": 20.0},
            {"freq": 5825.0, "name": "5G_Ch165", "bandwidth": 20.0},
        ]
        
        # Drone signature profiles
        self.drone_profiles = {
            "DJI_Phantom": {
                "control": [2400, 2483],  # 2.4GHz spread
                "video": [5725, 5850],    # 5.8GHz video
                "telemetry": [915],        # Telemetry
                "gps": [1575.42],          # GPS
                "signature_power": -45     # Typical drone signal strength
            },
            "FPV_Racer": {
                "control": [2400, 2483],
                "video": [5650, 5950],     # Wider 5GHz for analog
                "telemetry": [433],        # 433MHz telemetry
                "gps": [1575.42],
                "signature_power": -50
            }
        }
        
    def generate_noise_floor(self, freq_mhz):
        """Generate realistic noise floor with some variation"""
        # Higher frequencies typically have slightly higher noise
        freq_factor = math.log10(freq_mhz / 100) * 2
        return self.base_noise_floor + freq_factor + random.gauss(0, 2)
    
    def generate_background_signals(self, freq_mhz, timestamp):
        """Generate ambient RF environment (WiFi, cellular, etc.)"""
        power = self.generate_noise_floor(freq_mhz)
        
        # Add some periodic background signals
        if 2400 <= freq_mhz <= 2483:  # 2.4GHz WiFi band
            if random.random() < 0.3:  # 30% chance of WiFi activity
                power = max(power, -70 + random.gauss(0, 5))
        
        elif 5150 <= freq_mhz <= 5850:  # 5GHz band
            if random.random() < 0.2:  # 20% chance
                power = max(power, -75 + random.gauss(0, 5))
        
        elif 1920 <= freq_mhz <= 1980:  # Cellular uplink
            if random.random() < 0.4:
                power = max(power, -65 + random.gauss(0, 8))
                
        return power
    
    def generate_drone_signal(self, freq_mhz, drone_type, distance_factor=1.0):
        """Generate drone RF signature"""
        profile = self.drone_profiles[drone_type]
        signal_present = False
        power = self.generate_noise_floor(freq_mhz)
        
        # Check each drone frequency band
        for band_name, freqs in profile.items():
            if band_name == "signature_power":
                continue
                
            for f in freqs:
                if abs(freq_mhz - f) < 20:  # Within 20MHz
                    signal_present = True
                    # Signal strength decreases with distance
                    drone_power = profile["signature_power"] - (20 * math.log10(distance_factor))
                    # Add frequency hopping variation
                    drone_power += random.gauss(0, 3)
                    power = max(power, drone_power)
                    
        return power, signal_present
    
    def generate_spectrum_sweep(self, timestamp, drone_event=None):
        """Generate a full spectrum sweep"""
        spectrum_data = []
        
        # Sweep through frequency bands
        for band in self.frequency_bands:
            center_freq = band["freq"]
            
            # Sample multiple points across the bandwidth
            for offset in np.linspace(-band["bandwidth"]/2, band["bandwidth"]/2, 10):
                freq_mhz = center_freq + offset
                
                # Base signal
                power = self.generate_background_signals(freq_mhz, timestamp)
                
                # Add drone signal if present
                if drone_event:
                    drone_power, is_drone = self.generate_drone_signal(
                        freq_mhz, 
                        drone_event["type"],
                        drone_event["distance"]
                    )
                    if is_drone:
                        power = drone_power
                
                spectrum_data.append({
                    "freq_mhz": round(freq_mhz, 2),
                    "power_dbm": round(power, 1),
                    "bandwidth_khz": 100
                })
        
        return spectrum_data
    
    def generate_dataset(self, duration_seconds=60, sample_rate=2):
        """Generate complete dataset with drone events"""
        messages = []
        start_time = datetime.now()
        
        # Schedule drone events
        drone_events = [
            {"start": 15, "end": 25, "type": "DJI_Phantom", "name": "DJI Phantom Flyby"},
            {"start": 40, "end": 48, "type": "FPV_Racer", "name": "FPV Racer Pass"},
        ]
        
        for t in range(0, duration_seconds * sample_rate):
            timestamp = start_time + timedelta(seconds=t/sample_rate)
            current_second = t / sample_rate
            
            # Check for drone events
            drone_event = None
            for event in drone_events:
                if event["start"] <= current_second <= event["end"]:
                    # Calculate distance factor (approaching then departing)
                    progress = (current_second - event["start"]) / (event["end"] - event["start"])
                    distance = 1 + abs(progress - 0.5) * 2  # Closest at midpoint
                    drone_event = {
                        "type": event["type"],
                        "distance": distance,
                        "name": event["name"]
                    }
                    break
            
            # Generate spectrum sweep message
            spectrum_msg = {
                "messageId": "SPECTRUM_DATA",
                "timestamp": timestamp.isoformat(),
                "timestamp_unix": timestamp.timestamp(),
                "sweepNumber": t,
                "centerFreqMhz": 3000.0,  # Center of scan range
                "sweepWidthMhz": 6000.0,  # Width of scan
                "resolutionBandwidthKhz": 100,
                "detections": [],
                "spectrum": self.generate_spectrum_sweep(timestamp, drone_event)
            }
            
            # Add detection alerts
            if drone_event:
                spectrum_msg["detections"].append({
                    "type": "DRONE_SUSPECTED",
                    "confidence": 0.85 - (drone_event["distance"] - 1) * 0.2,
                    "drone_type": drone_event["type"],
                    "description": drone_event["name"],
                    "frequencies_detected": self.get_drone_frequencies(drone_event["type"])
                })
            
            messages.append(spectrum_msg)
            
            # Add status messages periodically
            if t % 10 == 0:  # Every 5 seconds
                messages.append({
                    "messageId": "ACTIVE_MODE_IND",
                    "timestamp": timestamp.isoformat(),
                    "activeMode": "Scanning",
                    "sweepType": "FULL_SPECTRUM",
                    "sweepSpeedGhzSec": 10.0
                })
            
            if t % 20 == 0:  # Every 10 seconds
                messages.append({
                    "messageId": "GPS_IND",
                    "timestamp": timestamp.isoformat(),
                    "gps": {
                        "fix": "3D_FIX",
                        "lat": 33.7490 + random.gauss(0, 0.0001),
                        "lon": -84.3880 + random.gauss(0, 0.0001),
                        "alt": 320.0 + random.gauss(0, 1),
                        "numSatellites": 8
                    }
                })
        
        return messages
    
    def get_drone_frequencies(self, drone_type):
        """Get list of frequencies where drone is detected"""
        profile = self.drone_profiles[drone_type]
        freqs = []
        for band_name, freq_list in profile.items():
            if band_name != "signature_power":
                freqs.extend(freq_list)
        return freqs
    
    def save_dataset(self, messages, filename):
        """Save messages to file"""
        with open(filename, 'w') as f:
            for msg in messages:
                f.write(json.dumps(msg) + '\n')
        print(f"Generated {len(messages)} messages")
        print(f"Dataset saved to: {filename}")


def main():
    simulator = RFDataSimulator()
    
    print("Generating RF sensor dataset with drone events...")
    messages = simulator.generate_dataset(duration_seconds=60, sample_rate=2)
    
    output_file = '/Users/tylerhouchin/code/demos/gpt-oss/MCOA/testing-sensor/rf_sensor_data.jsonl'
    simulator.save_dataset(messages, output_file)
    
    # Print summary
    spectrum_msgs = [m for m in messages if m['messageId'] == 'SPECTRUM_DATA']
    detection_msgs = [m for m in spectrum_msgs if len(m.get('detections', [])) > 0]
    
    print(f"\nDataset Summary:")
    print(f"  Total spectrum sweeps: {len(spectrum_msgs)}")
    print(f"  Sweeps with detections: {len(detection_msgs)}")
    print(f"  Detection rate: {len(detection_msgs)/len(spectrum_msgs)*100:.1f}%")
    

if __name__ == '__main__':
    main()