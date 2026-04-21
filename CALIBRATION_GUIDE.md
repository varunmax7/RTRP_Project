# ACS712 Current Sensor Calibration Guide

## ⚙️ Calibration Steps

### Step 1: Identify Your ACS712 Module
Check the label on your module. Common variants:

| Module | Sensitivity (mV/A) | Scale Value |
|--------|------------------|-------------|
| ACS712-5A | 185 | 0.185 |
| ACS712-20A | 100 | 0.100 |
| ACS712-30A | 66 | 0.066 |

### Step 2: Set Zero Voltage
The midpoint voltage (when no current flows) should be calibrated.

**Method 1: Disconnected Sensor**
1. Disconnect the motor/load
2. Run the code and note the voltage reading
3. This should be ~2.5V (half of 5V supply)
4. Update `zeroVoltage` in the code to match

**Method 2: Precise Calibration**
1. Compile and upload the basic code (without calibration)
2. Open Serial Monitor
3. Measure voltage with multimeter on A0
4. Update `zeroVoltage = measured_voltage;`

### Step 3: Verify with Known Load
1. Connect a known resistive load (e.g., light bulb, heater)
2. Measure the current with a multimeter or clamp meter
3. Compare with the Arduino reading
4. Adjust `sensitivity` if needed (usually ±5% accuracy is acceptable)

### Step 4: Update Code
```cpp
#define ACS_PIN A0
float sensitivity = 0.185;      // Change based on your module
float zeroVoltage = 2.5;        // Calibrated value
```

## 📊 Calibration Code Snippet

```cpp
void calibrate_acs712() {
  // Read 100 samples with no load
  float sum = 0;
  for(int i = 0; i < 100; i++) {
    int raw = analogRead(ACS_PIN);
    float voltage = raw * (5.0 / 1023.0);
    sum += voltage;
    delay(10);
  }
  float avg_voltage = sum / 100.0;
  Serial.print("Zero voltage: ");
  Serial.println(avg_voltage);
}
```

Run this in `setup()` once, note the value, then use it as `zeroVoltage`.

## 🧪 Testing Your Calibration

1. **No Load**: Should read ~0A
2. **Light Bulb (60W @ 120V)**: Should read ~0.5A
3. **Motor at Full Speed**: Should read 2-4A (depending on motor)

## 📈 Sample Calibrated Values

For the 3D printer creep detection:
- **Healthy**: ~1.2A motor current
- **Creep**: ~2.8A+ motor current

So your calibration should distinguish reliably between these ranges.
