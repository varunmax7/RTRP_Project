#!/usr/bin/env python3
"""Quick script to read Arduino serial output"""
import serial
import time
import sys

port = '/dev/cu.usbmodem1101'
baud = 9600

try:
    ser = serial.Serial(port, baud, timeout=2)
    print(f"Connected to {port}")
    print("Reading serial data for 10 seconds...\n")
    
    start_time = time.time()
    while time.time() - start_time < 10:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"Raw data: {line}")
    
    ser.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
