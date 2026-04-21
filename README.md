# 🖨️ 3D Printer Health Monitoring & ML-Based Detection System

Welcome to the **3D Printer Health Monitoring System**! This repository provides a complete hardware, firmware, and software ecosystem designed to monitor 3D printing tasks in real time. It uses a combination of analog sensors and machine learning to proactively classify the printer's performance layer-by-layer, predicting potential failures and mechanical creep before they ruin a print.

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

The system features both an **on-device OLED dashboard** for quick diagnostics at a glance, and a **local Flask web server dashboard** for remote monitoring.

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
Open your web browser and navigate to `http://localhost:5001`. You will see the dynamic updating dashboard with real-time graphs and predictions.

---

## 🔧 Calibration & Customization

Every 3D printer behaves differently. Your actual baseline for "Healthy" may look very different from our default thresholds.

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

## 🐛 Common Troubleshooting

* **Sensors reading "nan":** Check DHT wiring (Power, GND, Data Pin). Verify your pull-up resistors on the DHT data line.
* **Inaccurate Current Readings:** Ensure the ACS712 is powered with a clean 5V source. You may need to calibrate the `zeroVoltage` variable inside the C++ code.
* **OLED Blank:** Verify I2C address (usually `0x3C`, sometimes `0x3D`). Check SDA/SCL connections and ensure the `Adafruit_SSD1306` library is properly bundled in your PlatformIO setup.
* **Missing Flask Server Connection:** Confirm the `SERIAL_PORT` variable in `sensor_monitor.py` corresponds exactly to your active USB device path.

---

### File Size & Microcontroller Efficiency
This system is highly optimized. While the Random Forest model runs on the Python backend, the Arduino utilizes pre-calculated branching logic, requiring no intensive ML libraries on the board. The compiled C++ sketch takes roughly `~8KB` of program storage space, leaving plenty of overhead on the Arduino Micro.

Enjoy smarter, safer 3D printing!
