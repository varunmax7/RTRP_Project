#!/usr/bin/env python3
"""Diagnostic tool to check Arduino serial output format"""

import sys
sys.path.insert(0, '/Users/ramavathvarun/rtrp_ws/rtrp_project')

import serial
import time

port = '/dev/cu.usbmodem1101'
baud = 9600

print(f"Connecting to {port}...")
try:
    ser = serial.Serial(port, baud, timeout=2)
    time.sleep(2)
    print(f"✓ Connected!\n")
    print("Raw Arduino output (first 20 lines):\n")
    print("-" * 80)
    
    count = 0
    while count < 20:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"[{count+1}] {line}")
                
                # Try to parse it with our format
                if "LIVE DATA" in line:
                    print("    ✓ Contains 'LIVE DATA' - this is a data line!")
                    
                    try:
                        data = {}
                        
                        # Extract Nozzle
                        if "Nozzle:" in line:
                            nozzle_start = line.find("Nozzle:") + 7
                            nozzle_end = line.find(" C", nozzle_start)
                            nozzle = float(line[nozzle_start:nozzle_end].strip())
                            data['nozzle_temp'] = nozzle
                            print(f"    ✓ Nozzle: {nozzle}°C")
                        
                        # Extract Bed
                        if "Bed:" in line:
                            bed_start = line.find("Bed:") + 4
                            bed_end = line.find(" C", bed_start)
                            bed = float(line[bed_start:bed_end].strip())
                            data['bed_temp'] = bed
                            print(f"    ✓ Bed: {bed}°C")
                        
                        # Extract Current
                        if "Current:" in line:
                            current_start = line.find("Current:") + 8
                            current_end = line.find(" A", current_start)
                            current = float(line[current_start:current_end].strip())
                            data['current'] = current
                            print(f"    ✓ Current: {current}A")
                        
                        # Extract Vibrations
                        if "Vib:" in line:
                            vib_start = line.find("Vib:") + 4
                            vib_end = line.find(" pulses", vib_start)
                            vib = float(line[vib_start:vib_end].strip())
                            data['vib_per_min'] = vib
                            print(f"    ✓ Vibrations: {vib}")
                        
                        if len(data) == 4:
                            print(f"    ✅ COMPLETE: All 4 values parsed successfully!")
                        else:
                            print(f"    ⚠️  Incomplete: Only {len(data)}/4 values parsed")
                    except Exception as e:
                        print(f"    ❌ Parse error: {e}")
                
                count += 1
    
    print("-" * 80)
    ser.close()

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
