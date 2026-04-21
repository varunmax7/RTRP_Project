# Sensor Monitor - Real-Time Dashboard

This system displays all sensor values from your 3D printer health monitoring system on a web dashboard at **localhost:5001**. Sensor readings are collected every **10 seconds** and displayed in real-time.

## Features

✅ **Real-time Sensor Display** - Shows all 4 sensor values with 10-second intervals:
  - Nozzle Temperature (°C)
  - Bed Temperature (°C)
  - Motor Current (Amperes)
  - Vibrations (per minute)

✅ **Model Results** - Shows the health status:
  - HEALTHY ✅
  - CAUTION 🟡
  - CREEP ⚠️

✅ **Data History** - Displays last 100 readings in a table

✅ **Connection Status** - Shows whether you're using real Arduino or mock data

✅ **Beautiful Dashboard** - Modern responsive web interface

## Setup

### 1. Install Dependencies

```bash
cd /Users/ramavathvarun/rtrp_ws/rtrp_project
pip install -r requirements.txt
```

### 2. (Optional) Configure Arduino Serial Port

Open `sensor_monitor.py` and update this line with your Arduino's serial port:
```python
SERIAL_PORT = '/dev/cu.usbmodem14201'  # Change this to your port
```

Find your Arduino port:
- **macOS**: `ls /dev/tty.usb*` or `ls /dev/cu.usb*`
- **Linux**: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`
- **Windows**: Check Device Manager

### 3. Run the Server

```bash
python sensor_monitor.py
```

You should see:
```
 * Running on http://localhost:5001
 * Model Available: True
 * Sensor Interval: 10 seconds
```

### 4. Open Dashboard

Open your browser and go to: **http://localhost:5001**

## How It Works

### Arduino Data Format

If using a real Arduino, it should send sensor data in this format:
```
nozzle:200.5,bed:60.2,current:1.5,vib:45
```

### Classification Logic

The system uses either:
- **ML Model** (if `model/model.pkl` and `model/scaler.pkl` exist) - For more accurate predictions
- **Rule-Based Classification** (fallback) - Simple threshold-based logic:
  - **HEALTHY**: All sensors in healthy range
  - **CREEP**: 2+ sensors showing degradation
  - **CAUTION**: Mixed signals

### Sensor Thresholds (Rule-Based)

**HEALTHY Range:**
- Nozzle Temp: < 225°C
- Bed Temp: < 70°C
- Motor Current: < 1.8A
- Vibrations: < 70 vib/min

**CREEP/Degradation Range:**
- Nozzle Temp: > 235°C
- Bed Temp: > 72°C
- Motor Current: > 2.5A
- Vibrations: > 90 vib/min

## Data Collection Modes

### 1. **Real Arduino Mode** ✅
- Requires Arduino to send serial data every 10 seconds
- Connection status shows: "Connected to Arduino"
- Data source shows: "Real Arduino"

### 2. **Mock Data Mode** 🟡
- Generates realistic simulated sensor values
- Used when Arduino is not connected
- Connection status shows: "Simulated Data"
- Data source shows: "Mock Sensor (Simulated)"

The app automatically switches to mock mode if the Arduino port is not available.

## API Endpoints

### GET /
Main dashboard page

### GET /api/sensor-data
Returns all sensor readings with timestamps and status
```json
{
  "data": [
    {
      "timestamp": "2024-01-15 10:30:45",
      "nozzle_temp": 210.5,
      "bed_temp": 65.2,
      "current": 1.6,
      "vib_per_min": 55,
      "status": "HEALTHY"
    }
  ],
  "latest": {...},
  "model_available": true,
  "use_mock_data": false
}
```

### GET /api/status
Returns current system status
```json
{
  "status": "HEALTHY",
  "connected": true,
  "model_available": true,
  "reading_count": 45,
  "last_update": "2024-01-15 10:30:45"
}
```

## Features on Dashboard

### Sensor Cards
- Large display of current sensor values
- Visual progress bars showing value ranges
- Color-coded indicators

### Status Badge
- Shows overall system status (HEALTHY/CAUTION/CREEP)
- Located at the top of the dashboard

### Data History Table
- Shows last 100 readings
- Timestamped entries
- Color-coded status column

### Statistics Bar
- Total readings collected
- Collection interval (10 seconds)
- Data source (Real Arduino or Mock)
- Model status (ML Model or Rule-Based)

### Connection Indicator
- Live connection status
- Shows whether using real Arduino or simulated data

## Troubleshooting

### Dashboard shows "Waiting for sensor data..."
- The system needs time to collect the first reading (up to 10 seconds)
- Check that `sensor_monitor.py` is running
- Data updates every 10 seconds, be patient

### Arduino not connecting
- Board will auto-fall back to mock (simulated) data
- Check serial port in `sensor_monitor.py`
- Make sure Arduino is plugged in
- Try resetting the Arduino board

### Model not loading
- If you don't have trained models, it uses rule-based classification
- Train the model first: `python ml_train.py`
- This creates `model/model.pkl` and `model/scaler.pkl`

### Dashboard not loading
- Make sure Flask is installed: `pip install Flask`
- Check that port 5001 is not in use
- Try a different port by changing `port=5001` in the last line

## Notes

- **Collection Interval**: Sensor data is collected every 10 seconds
- **Data Retention**: Last 100 readings are kept in memory
- **Auto-refresh**: Dashboard updates every 1 second by checking for new data
- **Status Colors**:
  - 🟢 Green = HEALTHY
  - 🟡 Yellow = CAUTION
  - 🔴 Red = CREEP
