# 🖨️ 3D Printer Health Monitoring & ML-Based Detection System

Welcome to the **3D Printer Health Monitoring System** (RTRP)! This repository provides a complete hardware, firmware, and software ecosystem designed to monitor 3D printing tasks in real time. It uses a combination of analog sensors and machine learning to proactively classify the printer's performance layer-by-layer, predicting potential failures and mechanical creep before they ruin a print.

**Latest Version (v2.0):** Complete web dashboard with authentication, system control, real-time analytics, and RUL tracking. ✨

---

## 🛑 The Problem We're Solving

3D printing requires precise operating parameters over extended periods, often continuing unattended for dozens of hours. During these long prints, several invisible factors can compromise print quality or cause catastrophic failure:
1. **Thermal Runaway or Drift:** Temperatures can drift outside the safe operating zones for specific filaments.
2. **Mechanical Misalignment:** Mechanical vibrations increase over time, loosening belts, untightening screws, or misaligning axes (leading to layer shifts).
3. **Motor Resistance:** Stepper motors can experience binding or increased mechanical resistance, clearly reflecting as an abnormal spike in current draw.

Relying entirely on visual inspection or simple temperature thermal runaway protection is insufficient. By the time a print spaghetti unspools or an axis shifts, the damage is already done, leading to wasted time, wasted material, and potential hardware damage.

## 💡 Our Solution

We shift the paradigm from **reactive troubleshooting** to **predictive maintenance**. 
By capturing raw telemetry from multiple structural and environmental points—nozzle temperature, bed temperature, structural vibration, and stepper motor current—the system analyzes patterns in real-time. 

It assigns a physical health state to the printer:
* **✅ HEALTHY:** The machine is operating within expected, safe bounds.
* **⚠️ CREEP:** The machine is exhibiting structural or thermal deterioration (e.g., elevated temperatures, excessive vibrations, high motor loads). Immediate intervention is recommended.
* **🟡 CAUTION:** The machine is entering transitional zones; the print may be in jeopardy soon.

The system features both an **on-device OLED dashboard** for quick diagnostics at a glance, and a **responsive Flask web dashboard** for remote monitoring with authentication, real-time charts, and system controls.

---

## ✨ Key Features (v2.0)

### Dashboard & Web Interface
- 🔐 **Secure Login Authentication** - Session-based login with admin credentials
- 📊 **Real-Time Charts** - Interactive line charts showing sensor trends using Chart.js
- 📱 **Responsive UI** - Mobile-friendly design works on desktop, tablet, and phone
- 🎨 **Modern Design** - Clean Tailwind-based UI with status badges and health indicators
- 📥 **CSV Export** - Download sensor history and telemetry data
- 🔄 **Live Updates** - Auto-refresh every second for real-time monitoring

### System Control & Management
- ⏸️ **System Toggle Button** - Pause/Resume data collection with one click
- 🔒 **Thread-Safe Operations** - Robust pause/resume with mutex locking
- 💾 **SQLite Database** - Persistent storage of all sensor readings and analytics
- 📈 **RUL Tracking** - Remaining Useful Life calculation (48h, 12h, 6h, 1h based on health %)

### Sensor Integration
- 🌡️ **Nozzle Temperature** - Real-time hotend monitoring
- 🛏️ **Bed Temperature** - Heatbed thermal tracking
- ⚡ **Motor Current** - ACS712 sensor for load detection
- 📳 **Vibration Sensing** - Mechanical stress monitoring
- 🔄 **10-Second Intervals** - Continuous data collection loop

### Machine Learning
- 🤖 **ML-Based Classification** - scikit-learn Random Forest predictor
- 📊 **Feature Scaling** - StandardScaler normalized inputs
- 🎯 **Health Percentage** - Individual component health scores (0-100%)
- 🧠 **Rule-Based Fallback** - Works even without pre-trained models

### Progressive Web App
- 📲 **PWA Support** - Install as app on home screen
- 🌐 **Offline Caching** - Service worker for offline functionality
- 📋 **Manifest.json** - Web app metadata and configuration
- ⚡ **Fast Loading** - Optimized assets and caching strategies

---

## 🛠 Tech Stack & Architecture

### Hardware Components
* **Microcontroller:** Arduino Micro Board (or compatible ESP32/UNO depending on setup)
* **Hotend Temperature:** DHT11 Data Pin (monitors Nozzle Temp, expected 200-240°C)
* **Heatbed Temperature:** DHT11 Data Pin (monitors Bed Temp, expected 50-75°C)
* **Vibrational Stress:** Vibration Sensor (monitors mechanical shakes/bumps per minute)
* **Motor Current:** ACS712 Analog Current Sensor (monitors electrical load from motors)
* **Diagnostics Display:** 128x64 OLED (SSD1306) communicating via I2C (SDA/SCL)

### Software & Firmware
* **Embedded Development:** C++, PlatformIO framework
* **Backend / Telemetry Server:** Python, Flask server (`sensor_monitor.py`)
* **Machine Learning & Data Science:** `scikit-learn` for training predictive classifiers, `pandas`, `numpy`, `joblib`
* **Frontend:** HTML/JS graphical dashboard (`templates/dashboard.html`)
* **Communication:** PySerial fetching data continuously at 9600 baud.

---

## 🏗️ System Architecture & Data Flow

The architecture operates seamlessly between the physical Arduino sensors and the computational Python backend.

### 1. Embedded Data Collection (Arduino)
Every 500ms, the Arduino gathers raw metrics:
- Reads `nozzle_temp` from DHT1 (Pin 8)
- Reads `bed_temp` from DHT2 (Pin 9)
- Counts `vib_per_min` from the Vibration Sensor (Pin 7) over a 60-second window
- Calculates `motor_current` from the ACS712 sensor (Pin A0)

### 2. Validation & Classification
The microcontroller validates the data (checking for `NaN` readings). It then classifies the system health in real-time without needing a heavy mathematical library using rule-based metrics extracted from the ML model:

**HEALTHY Thresholds:** Nozzle < 225°C | Bed < 70°C | Current < 1.8A | Vibrations < 70/min
**CREEP Thresholds:** Nozzle > 235°C | Bed > 72°C | Current > 2.5A | Vibrations > 90/min

### 3. Output & Telemetry
- **On-Device:** The OLED immediately updates with the large status text and the 4 granular sensor values.
- **Serial Output:** The Arduino casts this validated data over the Serial port to the connected machine.
- **Web Dashboard:** The Python Flask server reads this Serial stream, optionally runs a highly accurate Random Forest model (`joblib` serialized `.pkl` files), and renders a beautiful live HTML dashboard.

---

## 🚀 Setup & Installation Guide

### Step 1: Clone and Prepare Firmware
1. Open this repository in **VS Code** with the **PlatformIO** extension installed.
2. The `platformio.ini` is already configured for the Arduino Micro. 
3. Connect your Arduino board.
4. Click the PlatformIO **Upload** button to build the C++ firmware (from `/src/`) and flash it to the board.

### Step 2: Set Up the Python Environment
Ensure you have Python 3.8+ installed. 
```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Train the Machine Learning Model
We've provided baseline data in `data/healthy_data.csv` and `data/creep_data.csv`. You need to train the classifier before starting the web dashboard:
```bash
python ml_train.py
# Or use python quick_train.py for faster output
```
This script will:
- Combine the CSV datasets.
- Train a `RandomForestClassifier`.
- Extract feature importance (showing which sensor best predicts a breakdown).
- Save the trained model and scaler to `model/model.pkl` and `model/scaler.pkl`.

### Step 4: Run the Live Dashboard
With the Arduino connected via USB, launch the Flask monitoring server:
```bash
# Ensure the Arduino serial port in sensor_monitor.py matches your system (e.g., /dev/cu.usbmodem1101 or COM3)
./run_sensor_monitor.sh
# Alternatively: python sensor_monitor.py
```

The server will start on `http://localhost:5001`

### Step 5: Access the Dashboard
1. Open your web browser and navigate to `http://localhost:5001`
2. You will be redirected to the login page
3. **Default Credentials:**
   - Username: `admin`
   - Password: `password123`
4. After login, you'll see the real-time dashboard with:
   - Live sensor readings (nozzle temp, bed temp, current, vibration)
   - System status badge (HEALTHY/CAUTION/CREEP)
   - RUL (Remaining Useful Life) estimation
   - Interactive sensor history charts
   - System control buttons (ON/OFF toggle, Export CSV)

**⚠️ Important Security Note:** Change the default admin password in production! Edit `sensor_monitor.py` line 38-39 to update credentials.

---

## � API Endpoints Reference

The Flask backend exposes the following endpoints:

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/` | GET | Required | Dashboard HTML page |
| `/login` | GET/POST | - | User authentication |
| `/logout` | GET | Required | Clear session |
| `/api/sensor-data` | GET | Required | Get all sensor readings & charts data |
| `/api/status` | GET | Required | Get system status summary |
| `/api/toggle-system` | POST | Required | Pause/Resume data collection |
| `/api/export-csv` | GET | Required | Download telemetry as CSV |

### Example API Usage
```bash
# Login
curl -c cookies.txt -d "username=admin&password=password123" http://localhost:5001/login

# Get sensor data
curl -b cookies.txt http://localhost:5001/api/sensor-data

# Toggle system (pause/resume)
curl -X POST -b cookies.txt http://localhost:5001/api/toggle-system

# Export CSV
curl -b cookies.txt http://localhost:5001/api/export-csv -o data.csv
```

---

## 📊 Database Schema

The SQLite database (`telemetry.db`) stores all sensor readings with the following structure:

```sql
CREATE TABLE sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    nozzle_temp REAL,
    bed_temp REAL,
    current REAL,
    vib_per_min REAL,
    status TEXT,
    rul INTEGER
)
```

Each row represents a single sensor reading collected every 10 seconds.

---

## 🎮 Dashboard Features Explained

### System Toggle Button
- **Location:** Header area next to status badge
- **Function:** Pauses data collection without disconnecting
- **Visual State:**
  - Green "SYSTEM ON" - Data collection active
  - Gray "SYSTEM OFF" - Data collection paused
- **Use Case:** Maintenance, testing, or temporary monitoring pause

### RUL (Remaining Useful Life) Display
Shows estimated hours before component failure:
- **48 Hours** - System HEALTHY (overall health ≥ 80%)
- **12 Hours** - System DEGRADING (overall health ≥ 60%)
- **6 Hours** - System in CAUTION (overall health ≥ 40%)
- **1 Hour** - System FAILING (overall health < 40%)

Calculated from individual component health percentages:
```
Overall Health = (Nozzle Health + Bed Health + Motor Health + Vibration Health) / 4
```

### Sensor Cards
Display real-time values with color-coded indicators:
- 🟢 Green border - Healthy range
- 🟡 Yellow border - Degrading range  
- 🔴 Red border - Failing range

### Charts
Interactive line charts showing 10-minute rolling history:
- Nozzle Temperature trend
- Bed Temperature trend
- Motor Current trend
- Vibration per minute trend

---

## 🔧 Hardware Connection Guide

### Current Sensor (ACS712) Connection
To measure motor current and enable full system diagnostics:

**Component:** ACS712-30A Current Sensor
**Arduino Pin:** A0 (Analog Input)
**Wiring:**
- VCC (Red) → Arduino 5V
- GND (Black) → Arduino GND
- OUT (Yellow) → Arduino A0

**Calibration:**
- Default zero voltage: 2.5V
- Sensitivity: 0.185 V/A
- Normal range: 0-30A (for 3D printer motors)

### Complete Sensor Pinout
```
Arduino Micro:
├── Pin 8 → DHT11 (Nozzle Temp)
├── Pin 9 → DHT11 (Bed Temp)
├── Pin 7 → Vibration Sensor (Digital)
├── A0 → ACS712 Current (Analog)
├── SDA → OLED SDA
├── SCL → OLED SCL
└── USB → Computer (9600 baud)

OLED I2C Address: 0x3C (or 0x3D if custom)
```

---

## 🔧 Customization & Tuning

### Re-tuning the System
1. **Collect Data:** Let your printer run a successful 12-hour print. Log the serial data into CSV format and append it to `data/healthy_data.csv`. Do the same when you notice a misbehaving print and append it to `data/creep_data.csv`.
2. **Examine CSV Format:** The CSV must precisely follow: `nozzle_temp,bed_temp,current,vib_per_min,status`
3. **Retrain Model:** Run `python ml_train.py`. The script will output new parameter rules.
4. **Update C++ Rules:** Open `src/test_with_ml.cpp` and update the constants (e.g., `HEALTHY_NOZZLE_MAX = 225.0;`) based on the Python script's recommendations. Re-flash the Arduino.

### Additional Guides in this Repo:
- **`CALIBRATION_GUIDE.md`**: Deep dive into calibrating the ACS712 current zero-voltage and vibration sensitivities.
- **`IMPLEMENTATION_CHECKLIST.md`**: Step-by-step physical hookup checklists.
- **`OLED_TROUBLESHOOTING.md`**: Guide for resolving I2C display problems (blank screens, wrong sizes).

---

## 📦 Project Structure

```
rtrp_project/
├── sensor_monitor.py           # Main Flask server (sensor collection, API, DB)
├── ml_train.py                 # ML model training script
├── quick_train.py              # Fast training for testing
├── templates/
│   ├── dashboard.html          # Main dashboard UI (responsive, PWA)
│   └── login.html              # Login authentication page
├── data/
│   ├── healthy_data.csv        # Training data (healthy prints)
│   └── creep_data.csv          # Training data (degraded prints)
├── model/
│   ├── model.pkl               # Trained Random Forest model
│   └── scaler.pkl              # Feature scaler for normalization
├── src/
│   └── test.cpp                # Arduino firmware (sensor + health calculation)
├── platformio.ini              # PlatformIO configuration
├── requirements.txt            # Python dependencies
└── telemetry.db               # SQLite database (auto-created)
```

---

## 🚀 Recent Updates (v2.0)

**Commit:** `c718ec9` - [View on GitHub](https://github.com/varunmax7/RTRP_Project)

### ✨ New Features
- ✅ System pause/resume toggle button in dashboard
- ✅ RUL calculation aligned between Arduino and web backend
- ✅ Secure login authentication system
- ✅ Thread-safe sensor data collection control
- ✅ SQLite telemetry database with persistent storage
- ✅ Interactive Chart.js graphs for sensor trending
- ✅ Responsive mobile-friendly dashboard
- ✅ CSV export functionality for data analysis
- ✅ PWA support with offline caching

### 🔧 Improvements
- Enhanced error handling and logging
- Optimized database queries
- Better real-time update mechanisms
- Improved thread synchronization
- Professional UI/UX with Tailwind CSS

---

## 🐛 Common Troubleshooting

### Dashboard Issues
* **"Address already in use" error:** Another process is using port 5001. Run `lsof -ti:5001 | xargs kill -9` to free the port.
* **Can't login:** Verify credentials are correct (default: admin/password123). Check `sensor_monitor.py` lines 38-39.
* **Session expires:** Your login session timed out. Refresh the page and log in again.
* **Blank dashboard:** Check browser console (F12) for JavaScript errors. Clear cache and refresh with Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows).

### Sensor Issues
* **Sensors reading "nan":** Check DHT wiring (Power, GND, Data Pin). Verify your pull-up resistors on the DHT data line.
* **Inaccurate Current Readings:** Ensure the ACS712 is powered with a clean 5V source. You may need to calibrate the `zeroVoltage` variable inside the C++ code.
* **OLED Blank:** Verify I2C address (usually `0x3C`, sometimes `0x3D`). Check SDA/SCL connections and ensure the `Adafruit_SSD1306` library is properly bundled in your PlatformIO setup.
* **Missing Flask Server Connection:** Confirm the `SERIAL_PORT` variable in `sensor_monitor.py` corresponds exactly to your active USB device path.

### System Toggle Issues
* **Toggle button doesn't respond:** Check browser console for network errors. Ensure you're logged in.
* **System won't pause:** Verify the thread lock is properly initialized in `sensor_monitor.py`. Restart the server if lock becomes deadlocked.
* **Data still collecting when OFF:** The collection loop may be in the middle of a 10-second cycle. Wait up to 10 seconds for pause to take effect.

### Database Issues
* **"Database locked" error:** Close other programs accessing the DB. Ensure only one instance of `sensor_monitor.py` is running.
* **Missing telemetry.db:** The database auto-creates on first run. If missing, restart the server or check file permissions.
* **CSV export empty:** Wait for at least one sensor reading cycle (~10 seconds) before exporting.

---

## 📝 File Size & Microcontroller Efficiency

This system is highly optimized:
- **Arduino Sketch:** ~8KB program storage (plenty of headroom on Micro)
- **Flask Backend:** Lightweight with minimal dependencies
- **Database:** SQLite for efficient data storage and querying
- **Frontend:** Optimized CSS/JS bundles with PWA caching

---

## 🤝 Contributing

Have improvements? Found a bug? Want to add a feature?
1. Fork the repository: [github.com/varunmax7/RTRP_Project](https://github.com/varunmax7/RTRP_Project)
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source. Check LICENSE file for details.

---

## ❤️ Acknowledgments

Built with:
- [Arduino](https://www.arduino.cc/) - Microcontroller platform
- [PlatformIO](https://platformio.org/) - Embedded development
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [scikit-learn](https://scikit-learn.org/) - Machine learning
- [Chart.js](https://www.chartjs.org/) - Data visualization
- [Adafruit Libraries](https://www.adafruit.com/) - Sensor libraries

---

**Enjoy smarter, safer 3D printing! 🚀**

*For questions or support, please open an issue on [GitHub](https://github.com/varunmax7/RTRP_Project/issues)*
