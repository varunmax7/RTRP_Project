"""
Real-time sensor monitoring web server
Displays sensor values and model predictions every 10 seconds on localhost:5001
"""

import time
import threading
import json
import re
import glob
from datetime import datetime
from collections import deque
import joblib
import numpy as np
from flask import Flask, render_template, jsonify
import serial
import sqlite3

import pandas as pd
from functools import wraps
from flask import session, redirect, url_for, request, Response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            # Check if HTMX request or regular JS fetch
            if request.headers.get('HX-Request') or request.headers.get('Accept', '').find('application/json') != -1:
                return {"error": "Unauthorized"}, 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

DB_FILE = 'telemetry.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      nozzle_temp REAL,
                      bed_temp REAL,
                      current REAL,
                      vib_per_min REAL,
                      status TEXT,
                      rul INTEGER)''')
        conn.commit()

init_db()

def calculate_rul(nozzle_temp, bed_temp, current, vib_per_min):
    """Calculate RUL based on overall health percentage (aligned with Arduino OLED)"""
    # First calculate individual health scores (0-100)
    nozzle_health = 100
    if nozzle_temp >= 245: nozzle_health = 0
    elif nozzle_temp >= 240: nozzle_health = 20
    elif nozzle_temp >= 235: nozzle_health = 40
    elif nozzle_temp >= 230: nozzle_health = 60
    elif nozzle_temp >= 225: nozzle_health = 80
    
    bed_health = 100
    if bed_temp >= 85: bed_health = 0
    elif bed_temp >= 80: bed_health = 20
    elif bed_temp >= 72: bed_health = 40
    elif bed_temp >= 70: bed_health = 80
    
    motor_health = 100
    if current >= 3.2: motor_health = 0
    elif current >= 2.8: motor_health = 20
    elif current >= 2.5: motor_health = 40
    elif current >= 2.0: motor_health = 60
    elif current >= 1.8: motor_health = 80
    
    vib_health = 100
    if vib_per_min >= 110: vib_health = 0
    elif vib_per_min >= 95: vib_health = 20
    elif vib_per_min >= 75: vib_health = 40
    elif vib_per_min >= 70: vib_health = 80
    
    # Calculate overall health percentage
    overall_health = (nozzle_health + bed_health + motor_health + vib_health) / 4
    
    # Map overall health to RUL hours (matching Arduino)
    if overall_health >= 80:
        return 48  # HEALTHY
    elif overall_health >= 60:
        return 12  # DEGRADING
    elif overall_health >= 40:
        return 6   # CAUTION
    else:
        return 1   # FAILING



# Configuration
SENSOR_INTERVAL = 10  # seconds between sensor readings
MAX_READINGS = 100  # max number of readings to keep in memory
SERIAL_PORT = '/dev/cu.usbmodem1101'  # Arduino serial port (auto-detected)
SERIAL_BAUD = 9600
ALLOW_MOCK_FALLBACK = True  # Enable mock data fallback for testing

# Global data storage
sensor_data = {
    'nozzle_temp': deque(maxlen=MAX_READINGS),
    'bed_temp': deque(maxlen=MAX_READINGS),
    'current': deque(maxlen=MAX_READINGS),
    'vib_per_min': deque(maxlen=MAX_READINGS),
    'status': deque(maxlen=MAX_READINGS),
    'rul': deque(maxlen=MAX_READINGS),
    'timestamps': deque(maxlen=MAX_READINGS)
}

# Model and scaler
try:
    model = joblib.load('model/model.pkl')
    scaler = joblib.load('model/scaler.pkl')
    MODEL_AVAILABLE = True
except:
    MODEL_AVAILABLE = False
    print("Warning: Could not load model/scaler. Using rule-based classification.")

# Rule-based thresholds (if model not available)
NOZZLE_HEALTHY_MAX = 225.0
BED_HEALTHY_MAX = 70.0
CURRENT_HEALTHY_MAX = 1.8
VIB_HEALTHY_MAX = 70

NOZZLE_DEGRADE_MIN = 235.0
BED_DEGRADE_MIN = 72.0
CURRENT_DEGRADE_MIN = 2.5
VIB_DEGRADE_MIN = 90

# Serial connection
ser = None
USE_MOCK_DATA = True

# System state
system_active = True  # Toggle this to pause/resume data collection
system_lock = threading.Lock()  # Thread-safe access to system_active


def find_arduino_port():
    """Find an available Arduino-like serial port on macOS/Linux."""
    candidates = []
    patterns = [
        "/dev/cu.usbmodem*",
        "/dev/cu.usbserial*",
        "/dev/tty.usbmodem*",
        "/dev/tty.usbserial*",
        "/dev/ttyACM*",
        "/dev/ttyUSB*",
    ]
    for pattern in patterns:
        candidates.extend(glob.glob(pattern))

    # Prefer usbmodem-style ports first
    candidates = sorted(candidates, key=lambda p: ("usbmodem" not in p, p))
    return candidates[0] if candidates else None


def parse_sensor_line(line):
    """Parse a serial line and return sensor dict when complete."""
    if not line:
        return None

    data = {}

    # Format 1: >>> LIVE DATA | Nozzle: 32.4 C | Bed: 35.4 C | Current: -0.65 A | Vib: 0.0 pulses/min
    nozzle_match = re.search(r"Nozzle:\s*([-+]?\d+(?:\.\d+)?)", line, re.IGNORECASE)
    bed_match = re.search(r"Bed:\s*([-+]?\d+(?:\.\d+)?)", line, re.IGNORECASE)
    current_match = re.search(r"Current:\s*([-+]?\d+(?:\.\d+)?)", line, re.IGNORECASE)
    vib_match = re.search(r"Vib:\s*([-+]?\d+(?:\.\d+)?)", line, re.IGNORECASE)

    if nozzle_match and bed_match and current_match and vib_match:
        data["nozzle_temp"] = float(nozzle_match.group(1))
        data["bed_temp"] = float(bed_match.group(1))
        data["current"] = float(current_match.group(1))
        data["vib_per_min"] = float(vib_match.group(1))
        return data

    # Format 2: nozzle:200.5,bed:60.2,current:1.5,vib:45
    if "," in line and ":" in line:
        for part in line.split(","):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            try:
                if key == "nozzle":
                    data["nozzle_temp"] = float(value)
                elif key == "bed":
                    data["bed_temp"] = float(value)
                elif key == "current":
                    data["current"] = float(value)
                elif key == "vib":
                    data["vib_per_min"] = float(value)
            except ValueError:
                continue
        if len(data) == 4:
            return data

    return None

def connect_serial():
    """Attempt to connect to Arduino via serial port"""
    global ser, USE_MOCK_DATA, SERIAL_PORT
    try:
        detected_port = find_arduino_port()
        if not detected_port:
            ser = None
            if ALLOW_MOCK_FALLBACK:
                USE_MOCK_DATA = True
            else:
                USE_MOCK_DATA = False
            print("⚠ No Arduino serial port detected. Waiting for device...")
            return False

        SERIAL_PORT = detected_port

        # Close any existing connection
        if ser:
            try:
                ser.close()
            except:
                pass
        
        # Open new connection with proper settings
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUD,
            timeout=1,
            write_timeout=2
        )
        time.sleep(2)  # Wait for Arduino to initialize
        
        # Flush any buffered data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        USE_MOCK_DATA = False
        print(f"✓ Connected to {SERIAL_PORT}")
        return True
    except Exception as e:
        print(f"⚠ Could not connect to serial port: {e}")
        if ALLOW_MOCK_FALLBACK:
            print("  Using mock sensor data instead.")
            USE_MOCK_DATA = True
        else:
            print("  Mock fallback is disabled. Waiting for real Arduino data.")
            USE_MOCK_DATA = False
        return False

def read_sensor_data():
    """Read sensor data from Arduino or mock data"""
    if USE_MOCK_DATA and ALLOW_MOCK_FALLBACK:
        return generate_mock_sensor_data()
    else:
        return read_serial_sensor_data()

def generate_mock_sensor_data():
    """Generate realistic mock sensor data for testing"""
    import random
    
    # Generate realistic sensor values
    nozzle_temp = 200 + random.gauss(15, 5)  # Around 215°C with variation
    bed_temp = 60 + random.gauss(5, 3)       # Around 65°C with variation
    current = 1.5 + random.gauss(0.2, 0.15)  # Around 1.7A with variation
    vib_per_min = 50 + random.gauss(10, 5)   # Around 60 with variation
    
    # Ensure valid ranges
    nozzle_temp = max(0, min(300, nozzle_temp))
    bed_temp = max(0, min(100, bed_temp))
    current = max(0, min(5, current))
    vib_per_min = max(0, min(200, vib_per_min))
    
    return {
        'nozzle_temp': round(nozzle_temp, 2),
        'bed_temp': round(bed_temp, 2),
        'current': round(current, 2),
        'vib_per_min': round(vib_per_min, 2)
    }

def read_serial_sensor_data():
    """Read sensor data from Arduino serial port"""
    global ser, USE_MOCK_DATA
    try:
        if not ser or not ser.is_open:
            return None

        # Drain buffered lines and keep the most recent valid sensor frame.
        latest_data = None
        max_lines = 120
        lines_read = 0
        while ser.in_waiting and lines_read < max_lines:
            lines_read += 1
            try:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
            except Exception:
                continue
            parsed = parse_sensor_line(line)
            if parsed is not None:
                latest_data = parsed

        return latest_data
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
        # Try to reconnect on next attempt
        if ser and ser.is_open:
            try:
                ser.close()
            except:
                pass
        ser = None
        if ALLOW_MOCK_FALLBACK:
            USE_MOCK_DATA = True
        else:
            USE_MOCK_DATA = False
    except Exception as e:
        print(f"Unexpected error reading serial: {e}")
    
    return None

def classify_status(nozzle_temp, bed_temp, current, vib_per_min):
    """Classify sensor status using ML model or rule-based thresholds"""
    
    if MODEL_AVAILABLE:
        try:
            # Prepare features for model
            features = np.array([[nozzle_temp, bed_temp, current, vib_per_min]])
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)[0]
            
            # 0 = healthy, 1 = creep
            status = "CREEP" if prediction == 1 else "HEALTHY"
            return status
        except Exception as e:
            print(f"Model prediction error: {e}")
    
    # Rule-based classification (fallback)
    creep_count = 0
    healthy_count = 0
    
    if nozzle_temp > NOZZLE_DEGRADE_MIN:
        creep_count += 1
    elif nozzle_temp < NOZZLE_HEALTHY_MAX:
        healthy_count += 1
    
    if bed_temp > BED_DEGRADE_MIN:
        creep_count += 1
    elif bed_temp < BED_HEALTHY_MAX:
        healthy_count += 1
    
    if current > CURRENT_DEGRADE_MIN:
        creep_count += 1
    elif current < CURRENT_HEALTHY_MAX:
        healthy_count += 1
    
    if vib_per_min > VIB_DEGRADE_MIN:
        creep_count += 1
    elif vib_per_min < VIB_HEALTHY_MAX:
        healthy_count += 1
    
    if creep_count >= 2:
        return "CREEP"
    elif healthy_count >= 3:
        return "HEALTHY"
    else:
        return "CAUTION"

def sensor_collection_loop():
    """Background thread to collect sensor data every 10 seconds"""
    global ser, USE_MOCK_DATA, system_active
    
    reconnect_counter = 0
    
    # Attempt to connect to serial
    connect_serial()
    
    while True:
        try:
            time.sleep(SENSOR_INTERVAL)
            
            # Check if system is paused
            with system_lock:
                if not system_active:
                    continue  # Skip data collection if system is paused

            # Reconnect when serial is missing/closed, or periodically while in mock mode.
            if ser is None or (hasattr(ser, "is_open") and not ser.is_open):
                connect_serial()
            elif USE_MOCK_DATA and reconnect_counter % 5 == 0:
                connect_serial()
            reconnect_counter += 1
            
            # Read sensor data
            data = read_sensor_data()
            
            if data is None or len(data) != 4:
                if reconnect_counter % 3 == 0:
                    print("Waiting for real sensor frames from Arduino...")
                continue
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Classify status
            status = classify_status(
                data['nozzle_temp'],
                data['bed_temp'],
                data['current'],
                data['vib_per_min']
            )
            
            # Calculate RUL
            rul = calculate_rul(
                data['nozzle_temp'],
                data['bed_temp'],
                data['current'],
                data['vib_per_min']
            )
            
            # Store data
            sensor_data['nozzle_temp'].append(data['nozzle_temp'])
            sensor_data['bed_temp'].append(data['bed_temp'])
            sensor_data['current'].append(data['current'])
            sensor_data['vib_per_min'].append(data['vib_per_min'])
            sensor_data['status'].append(status)
            sensor_data['rul'].append(rul)
            sensor_data['timestamps'].append(timestamp)
            
            # Print to console
            print(f"[{timestamp}] Temp: {data['nozzle_temp']}°C | Bed: {data['bed_temp']}°C | Current: {data['current']}A | Vib: {data['vib_per_min']} | Status: {status}")
        
        except Exception as e:
            print(f"Error in sensor collection loop: {e}")

# Start background thread
sensor_thread = threading.Thread(target=sensor_collection_loop, daemon=True)
sensor_thread.start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication handler"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials'), 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/sensor-data')
@login_required
def get_sensor_data():
    """API endpoint to get latest sensor data"""
    detected_port = find_arduino_port()
    serial_connected = bool(ser and getattr(ser, "is_open", False) and detected_port)

    if not sensor_data['timestamps']:
        return jsonify({
            'data': [],
            'latest': None,
            'model_available': MODEL_AVAILABLE,
            'use_mock_data': USE_MOCK_DATA,
            'serial_connected': serial_connected,
            'arduino_port': detected_port
        })
    
    # Prepare response data
    readings = []
    for i in range(len(sensor_data['timestamps'])):
        readings.append({
            'timestamp': sensor_data['timestamps'][i],
            'nozzle_temp': sensor_data['nozzle_temp'][i],
            'bed_temp': sensor_data['bed_temp'][i],
            'current': sensor_data['current'][i],
            'vib_per_min': sensor_data['vib_per_min'][i],
            'status': sensor_data['status'][i],
            'rul': sensor_data['rul'][i]
        })
    
    latest = readings[-1] if readings else None
    
    return jsonify({
        'data': readings,
        'latest': latest,
        'model_available': MODEL_AVAILABLE,
        'use_mock_data': USE_MOCK_DATA,
        'serial_connected': serial_connected,
        'arduino_port': detected_port
    })

@app.route('/api/status')
@login_required
def get_status():
    """API endpoint to get current status"""
    detected_port = find_arduino_port()
    serial_connected = bool(ser and getattr(ser, "is_open", False) and detected_port)

    if not sensor_data['timestamps']:
        return jsonify({
            'status': 'No data yet',
            'connected': serial_connected,
            'arduino_port': detected_port
        })
    
    latest_status = sensor_data['status'][-1]
    
    return jsonify({
        'status': latest_status,
        'connected': serial_connected,
        'model_available': MODEL_AVAILABLE,
        'reading_count': len(sensor_data['timestamps']),
        'last_update': sensor_data['timestamps'][-1],
        'arduino_port': detected_port
    })


@app.route('/api/export-csv')
@login_required
def export_csv():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM sensor_data", conn)
        return Response(df.to_csv(index=False), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=sensor_history.csv"})

@app.route('/api/toggle-system', methods=['POST'])
@login_required
def toggle_system():
    """Toggle system active/pause state"""
    global system_active
    with system_lock:
        system_active = not system_active
        state = system_active
    return jsonify({'is_active': state})

if __name__ == '__main__':
    print(f"Starting Sensor Monitor Web Server on http://localhost:5001")
    print(f"Model Available: {MODEL_AVAILABLE}")
    print(f"Sensor Interval: {SENSOR_INTERVAL} seconds")
    app.run(debug=False, host='localhost', port=5001, use_reloader=False)
