"""
System Architecture Overview

This file describes how the ML-based printer monitoring system works
"""

# 🏗️ SYSTEM ARCHITECTURE
# =======================

"""
┌─────────────────────────────────────────────────────────────────────┐
│                    3D PRINTER HEALTH MONITORING                     │
│                      ML-Based Detection System                      │
└─────────────────────────────────────────────────────────────────────┘

HARDWARE LAYER (Arduino Micro Board)
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  PIN 8 ──────> DHT11 ─────> Nozzle Temperature (200-240°C expected) │
│                                                                       │
│  PIN 9 ──────> DHT11 ─────> Bed Temperature (50-75°C expected)      │
│                                                                       │
│  PIN 7 ──────> Vibration Sensor ──> Vibrations/minute (0-150 range) │
│                                                                       │
│  PIN A0 ─────> ACS712 Current ──> Motor Current (0-5A range)        │
│                                                                       │
│  SDA/SCL ────> OLED SSD1306 ──> 128x64 Display Output               │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

DATA FLOW
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  1. SENSOR READING (every 500ms in loop())                          │
│     ├─ Read nozzle_temp from DHT1                                   │
│     ├─ Read bed_temp from DHT2                                      │
│     ├─ Count vibrations for 60 seconds                              │
│     └─ Calculate motor_current from ACS712                          │
│                                                                       │
│  2. VALIDATION                                                       │
│     └─ Check for sensor errors (NaN values)                         │
│                                                                       │
│  3. ML CLASSIFICATION (Rule-based)                                  │
│     ├─ Compare each sensor to HEALTHY thresholds                    │
│     ├─ Compare each sensor to CREEP thresholds                      │
│     └─ Output: HEALTHY, CREEP, or CAUTION                           │
│                                                                       │
│  4. DISPLAY OUTPUT                                                  │
│     ├─ Show large status text (HEALTHY/CREEP/CAUTION)               │
│     ├─ Show 4 sensor values                                         │
│     └─ Update every 500ms                                           │
│                                                                       │
│  5. SERIAL DEBUG (9600 baud)                                        │
│     └─ Output all values + status for troubleshooting               │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

CLASSIFICATION LOGIC
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  For each of 4 sensors, increment score:                            │
│                                                                       │
│  HEALTHY PARAMETERS:                                                │
│    ✓ nozzle_temp < 225°C          → healthy_score++                 │
│    ✓ bed_temp < 70°C              → healthy_score++                 │
│    ✓ current < 1.8A               → healthy_score++                 │
│    ✓ vib_per_min < 70             → healthy_score++                 │
│                                                                       │
│  CREEP PARAMETERS:                                                  │
│    ✗ nozzle_temp > 235°C          → creep_score++                   │
│    ✗ bed_temp > 72°C              → creep_score++                   │
│    ✗ current > 2.5A               → creep_score++                   │
│    ✗ vib_per_min > 90             → creep_score++                   │
│                                                                       │
│  DECISION:                                                           │
│    if (creep_score >= 3)           → "CREEP"    ⚠️                  │
│    else if (healthy_score >= 3)    → "HEALTHY"  ✅                  │
│    else                            → "CAUTION"  🟡                  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

TRAINING DATA PIPELINE (Python)
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  CSV Files (data/)                                                  │
│    ├─ healthy_data.csv (20 samples of normal operation)             │
│    └─ creep_data.csv (20 samples of creep behavior)                 │
│                 ↓                                                    │
│          [Load & Combine]                                            │
│                 ↓                                                    │
│          [Scale Features] (StandardScaler)                           │
│                 ↓                                                    │
│    [Train Model] (RandomForestClassifier)                           │
│                 ↓                                                    │
│          [Extract Parameters]                                        │
│                 ├─ Normalization mean values                        │
│                 ├─ Normalization std values                         │
│                 ├─ Feature importance                               │
│                 └─ Thresholds for Arduino                           │
│                 ↓                                                    │
│  Arduino Code (src/)                                                │
│    └─ test_with_ml.cpp (embeds thresholds in code)                 │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

DEPENDENCIES
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  ARDUINO Libraries (via PlatformIO):                                │
│    ├─ Adafruit_GFX (graphics for OLED)                              │
│    ├─ Adafruit_SSD1306 (OLED display driver)                        │
│    ├─ DHT sensor library (temperature sensors)                      │
│    └─ Wire (I2C communication)                                      │
│                                                                       │
│  Python Libraries:                                                  │
│    ├─ scikit-learn (ML training)                                    │
│    ├─ pandas (data manipulation)                                    │
│    ├─ numpy (numerical operations)                                  │
│    └─ joblib (model serialization)                                  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

PARAMETER TUNING FLOWCHART
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  Collect Real Printer Data (24-48 hours)                            │
│          ↓                                                            │
│  Label samples as "healthy" or "creep"                              │
│          ↓                                                            │
│  Add to data/healthy_data.csv or creep_data.csv                     │
│          ↓                                                            │
│  Run: python3 quick_train.py                                        │
│          ↓                                                            │
│  ┌─ Check Feature Importance ─────────┐                             │
│  │ Which sensor best predicts creep?  │                             │
│  └────────────────────────────────────┘                             │
│          ↓                                                            │
│  ┌─ Check New Thresholds ─────────────┐                             │
│  │ Are thresholds different?          │                             │
│  └────────────────────────────────────┘                             │
│          ↓         (if YES)                                          │
│  Update Constants in test_with_ml.cpp                               │
│          ↓                                                            │
│  Rerun on printer, check new accuracy                               │
│          ↓                                                            │
│  ┌─ Achieve > 95% Accuracy? ──────────┐                             │
│  │ YES → Deploy to production          │                             │
│  │ NO  → Collect more training data    │                             │
│  └────────────────────────────────────┘                             │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

FILE SIZE & MEMORY USAGE
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  Arduino Memory (Arduino Micro: 32KB total):                        │
│    ├─ Sketch Size: ~8KB (test_with_ml.cpp compiled)                 │
│    ├─ RAM Usage: ~2KB (variables + buffers)                         │
│    └─ Available: ~22KB (healthy margin)                             │
│                                                                       │
│  Python Training:                                                   │
│    ├─ Dataset Size: ~5KB (40 samples)                               │
│    ├─ Model Size: ~50KB (scaler.pkl + model.pkl)                    │
│    └─ Scripts: ~30KB Total                                          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

KEY ADVANTAGES OF THIS APPROACH
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  ✅ No ML Library Needed - Pure threshold logic                      │
│  ✅ Very Fast - <1ms prediction time                                │
│  ✅ Low Memory - Fits easily on Arduino Micro                        │
│  ✅ Interpretable - Easy to understand thresholds                    │
│  ✅ Easy to Debug - Serial output shows all values                   │
│  ✅ Easy to Improve - Just add more training data                    │
│  ✅ No Wireless Needed - Standalone operation                        │
│  ✅ Extensible - Can add more sensors/parameters anytime            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
"""

# HOW TO READ OLED DISPLAY
print("""
OLED Display Layout (128x64 pixels):

┌──────────────────────┐
│    [BIG STATUS]      │  Lines 0-15: Large text (28x28 px font)
│   HEALTHY CREEP CAU  │  Shows: HEALTHY / CREEP / CAUTION
├──────────────────────┤
│ Noz: 210.5C          │  Lines 20-55: Sensor values (8x8 px font)
│ Bed: 60.2C           │  4 Lines total = 4 sensor readings
│ Curr: 1.20A          │  
│ Vib: 45/min          │  Updated every 500ms
└──────────────────────┘

Expected update frequency: 2 times per second
""")

# TYPICAL SENSOR RANGES
print("""
TYPICAL SENSOR VALUE RANGES FOR 3D PRINTER:

Nozzle Temperature:           Bed Temperature:
  Idle:   20-30°C               Idle:   20-30°C
  Heating: 100-200°C            Heating: 30-60°C
  Printing: 210-220°C (normal)  Ready: 60-65°C
  Creep: 235-250°C              Creep: 72-85°C

Motor Current:                Vibrations per Minute:
  Idle: 0-0.1A                  Idle: 0-5 /min
  Moving: 0.5-1.2A (normal)     Printing: 30-60 /min (normal)
  Creep: 2.5-4.0A               Creep: 90-150+ /min
  Overload: >4.0A               Mechanical issue: >150 /min

These ranges are approximate and depend on your specific printer!
Calibration is IMPORTANT for accurate detection.
""")
