#!/usr/bin/env python3
"""
Deep scan of sensor data to find any actual RF measurements
"""

import json
from pathlib import Path
from collections import Counter

def deep_scan():
    data_dir = Path('/Users/tylerhouchin/code/demos/gpt-oss/MCOA/some_files')
    
    # Track all unique message types and fields
    message_types = Counter()
    all_fields = set()
    unique_messages = []
    
    # Sample different files
    files = sorted(data_dir.glob("*.txt"))
    
    print("Scanning for unique message patterns...")
    
    for file_idx, file_path in enumerate(files):
        print(f"\nScanning {file_path.name}...")
        
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line_num > 1000 and file_idx > 3:  # Sample first 1000 from first 4 files
                    break
                    
                try:
                    msg_str = line.strip()
                    if msg_str.startswith('"') and msg_str.endswith('"'):
                        msg_str = json.loads(msg_str)
                    msg = json.loads(msg_str)
                    
                    msg_id = msg.get('messageId', 'UNKNOWN')
                    message_types[msg_id] += 1
                    
                    # Collect all field names
                    all_fields.update(msg.keys())
                    
                    # Look for any message that's NOT the common 4 types
                    if msg_id not in ['REMOTE_JOIN_RESP', 'GPS_IND', 'BATTERY_IND', 'ACTIVE_MODE_IND']:
                        print(f"  FOUND DIFFERENT MESSAGE TYPE: {msg_id} at line {line_num}")
                        unique_messages.append(msg)
                    
                    # Check for FFT, spectrum, or signal data
                    for key in msg.keys():
                        if any(term in key.lower() for term in ['fft', 'spectrum', 'signal', 'power', 'dbm', 'freq', 'sweep_data', 'iq']):
                            if key not in ['sweepSpeedGhzSec', 'minFFTBinaryDataDbm', 'maxFFTBinaryDataDbm', 'sweepFreqResolutionsHz', 'maxIQSampleRateHz', 'minSysFreqHz', 'maxSysFreqHz', 'minRxFreqHz']:
                                print(f"  POTENTIAL DATA FIELD: {key} = {msg.get(key)}")
                    
                    # Check for nested data structures that might contain measurements
                    for key, value in msg.items():
                        if isinstance(value, dict) and key not in ['gps', 'receiverInfo']:
                            print(f"  NESTED OBJECT: {key} with keys: {value.keys()}")
                        elif isinstance(value, list) and len(value) > 0 and key not in ['sweepFreqResolutionsHz']:
                            print(f"  ARRAY FIELD: {key} with {len(value)} items")
                            if len(value) > 5:  # Could be data array
                                print(f"    Sample: {value[:5]}...")
                                
                except Exception as e:
                    pass
    
    print("\n" + "="*60)
    print("SCAN SUMMARY")
    print("="*60)
    print(f"\nMessage Type Distribution:")
    for msg_type, count in message_types.most_common():
        print(f"  {msg_type}: {count}")
    
    print(f"\nAll Fields Found:")
    for field in sorted(all_fields):
        print(f"  - {field}")
    
    print(f"\nUnique/Different Messages Found: {len(unique_messages)}")
    
    # Check if there's any variation in the data
    print("\n" + "="*60)
    print("CHECKING FOR DATA VARIATIONS")
    print("="*60)
    
    # Check endpointTime variations
    endpoint_times = set()
    pass_numbers = set()
    active_modes = set()
    sweep_types = set()
    
    for file_path in files[:2]:  # Check first 2 files
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line_num > 500:
                    break
                try:
                    msg_str = line.strip()
                    if msg_str.startswith('"') and msg_str.endswith('"'):
                        msg_str = json.loads(msg_str)
                    msg = json.loads(msg_str)
                    
                    if 'endpointTime' in msg:
                        endpoint_times.add(msg['endpointTime'])
                    if 'passNumber' in msg:
                        pass_numbers.add(msg['passNumber'])
                    if 'activeMode' in msg:
                        active_modes.add(msg['activeMode'])
                    if 'sweepType' in msg:
                        sweep_types.add(msg['sweepType'])
                        
                except:
                    pass
    
    print(f"Unique endpoint times: {len(endpoint_times)} - {list(endpoint_times)[:5]}")
    print(f"Unique pass numbers: {len(pass_numbers)} - {list(pass_numbers)}")
    print(f"Active modes: {active_modes}")
    print(f"Sweep types: {sweep_types}")

if __name__ == '__main__':
    deep_scan()