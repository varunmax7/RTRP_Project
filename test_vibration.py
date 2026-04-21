#!/usr/bin/env python3
"""
Quick diagnostic to test if vibrations are being counted
Shows real-time vibration values from Arduino
"""
import sys
sys.path.insert(0, '/Users/ramavathvarun/rtrp_ws/rtrp_project')

import serial
import time
import re

port = '/dev/cu.usbmodem1101'
baud = 9600

print("=" * 80)
print("VIBRATION SENSOR DIAGNOSTIC")
print("=" * 80)
print(f"\nConnecting to {port}...\n")

try:
    ser = serial.Serial(port, baud, timeout=2)
    time.sleep(2)
    
    print("✓ Connected! Reading sensor data...\n")
    print("Watching for LIVE DATA lines and extracting vibration values\n")
    print("-" * 80)
    print(f"{'Time':<12} {'Vibration':<15} {'Nozzle':<12} {'Bed':<12} {'Current':<12}")
    print("-" * 80)
    
    vibration_values = []
    
    for i in range(30):  # Read 30 lines
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if "LIVE DATA" in line:
                # Extract all sensor values
                try:
                    # Pattern: ">>> LIVE DATA | Nozzle: 32.4 C | Bed: 35.4 C | Current: -0.65 A | Vib: 0.0 pulses/min"
                    nozzle_match = re.search(r'Nozzle:\s+([\d.]+)\s+C', line)
                    bed_match = re.search(r'Bed:\s+([\d.]+)\s+C', line)
                    current_match = re.search(r'Current:\s+([-\d.]+)\s+A', line)
                    vib_match = re.search(r'Vib:\s+([\d.]+)\s+pulses', line)
                    
                    if all([nozzle_match, bed_match, current_match, vib_match]):
                        nozzle = float(nozzle_match.group(1))
                        bed = float(bed_match.group(1))
                        current = float(current_match.group(1))
                        vib = float(vib_match.group(1))
                        
                        timestamp = time.strftime('%H:%M:%S')
                        print(f"{timestamp:<12} {vib:<15.1f} {nozzle:<12.1f} {bed:<12.1f} {current:<12.2f}")
                        
                        vibration_values.append(vib)
                        
                except Exception as e:
                    print(f"Parse error: {e}")
    
    print("-" * 80)
    
    # Analyze vibration readings
    if vibration_values:
        print(f"\n📊 Vibration Analysis:")
        print(f"   Total readings: {len(vibration_values)}")
        print(f"   Min value: {min(vibration_values):.1f}")
        print(f"   Max value: {max(vibration_values):.1f}")
        print(f"   Avg value: {sum(vibration_values)/len(vibration_values):.1f}")
        print(f"   Non-zero readings: {sum(1 for v in vibration_values if v > 0)}")
        
        if all(v == 0 for v in vibration_values):
            print("\n❌ PROBLEM: All vibration readings are 0!")
            print("\nPossible causes:")
            print("  1. Vibration sensor not connected properly")
            print("  2. Sensor pin (7) not receiving signals")
            print("  3. Sensor needs debouncing (too much noise)")
            print("  4. Sensor threshold too high")
            print("\nFix: Check Arduino PIN 7 connection and vibration sensor wiring")
        else:
            print("\n✅ Vibrations ARE being detected! Values look good.")
    
    ser.close()

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
