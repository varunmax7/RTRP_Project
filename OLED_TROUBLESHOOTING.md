# 🔧 OLED Display Troubleshooting Guide

## ❌ "Nothing Shows on OLED" - Quick Fixes

Follow these steps in order:

---

## **STEP 1: Check Physical Wiring** (Do This First!)

### Arduino Micro I2C Pins:
```
SDA → Pin A4 (or marked SDA on board)
SCL → Pin A5 (or marked SCL on board)
VCC → +5V
GND → GND
```

### OLED Module Pins:
```
GND  → Arduino GND (BLACK wire)
VCC  → Arduino +5V (RED wire)
SDA  → Arduino A4  (GREEN/YELLOW wire)
SCL  → Arduino A5  (BLUE/PURPLE wire)
```

**Checklist:**
- [ ] All 4 wires connected firmly
- [ ] No loose connections
- [ ] SDA and SCL are correct (not swapped!)
- [ ] Power wires on correct polarity

---

## **STEP 2: Update platformio.ini (If Needed)**

Check if this library is listed:
```ini
[env:micro]
platform = atmelavr
board = micro
framework = arduino
lib_deps =
    adafruit/Adafruit GFX Library
    adafruit/Adafruit SSD1306
    adafruit/DHT sensor library
```

If `Adafruit SSD1306` is missing, add it. Then:
```bash
platformio lib update
```

---

## **STEP 3: Run the Simple OLED Test**

Replace the main code with the simple test:

```bash
# Temporarily rename your current code
mv src/test_with_ml.cpp src/test_with_ml.cpp.bak

# Copy test code
cp src/oled_simple_test.cpp src/test.cpp

# Upload
platformio run --target upload
```

**Open Serial Monitor:**
```bash
platformio device monitor --baud 9600
```

### Expected Output:
```
Starting OLED Simple Test...
Trying address 0x3C... SUCCESS!
```

### What You Should See on OLED:
```
OLED TEST
========
If you see this,
OLED is working!
```

**If you see this** → Jump to STEP 5

---

## **STEP 4: Diagnose I2C Address**

If simple test failed, run the diagnostic:

```bash
# Copy diagnostic code
cp src/oled_diagnostic.cpp src/test.cpp

# Upload and monitor
platformio run --target upload
platformio device monitor --baud 9600
```

**Will show:**
```
=== OLED DIAGNOSTIC TEST ===

Step 1: Scanning I2C addresses...
Scanning...
I2C device found at address 0x3C (decimal: 60)
  ^ This looks like your OLED display!
```

### If it finds 0x3D instead of 0x3C:
**This is the problem!** Your address is different.

**Fix:**
In `src/test_with_ml.cpp`, find this line:
```cpp
if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
```

Change `0x3C` to `0x3D`:
```cpp
if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {
```

### If it finds NO I2C devices:
**Wiring problem!** Check:
1. SDA/SCL not swapped
2. All wires firmly connected
3. Try different USB cable (sometimes power issue)
4. Check for cold solder joints on OLED module

---

## **STEP 5: Restore Your ML Code**

Once OLED is confirmed working:

```bash
# Restore your ML code
mv src/test_with_ml.cpp.bak src/test_with_ml.cpp

# Apply the address fix (if needed from STEP 4)
# Edit platformio.ini or code to use correct address

# Upload
platformio run --target upload

# Monitor
platformio device monitor --baud 9600
```

---

## **Common Issues & Solutions**

| Symptom | Cause | Solution |
|---------|-------|----------|
| Serial Monitor shows "OLED init failed!" | I2C address wrong | Find address with diagnostic, update code |
| Blank OLED (no text) | SDA/SCL reversed | Swap SDA ↔ SCL wires |
| OLED very dim/bright | Contrast setting | Edit OLED code: `display.setContrast(128)` |
| Random pixels/garbage | I2C pull-up issue | Add 4.7kΩ resistors to SDA & SCL |
| No I2C devices found | Wiring disconnected | Recheck all 4 wire connections |

---

## **Code Fixes Cheat Sheet**

### Fix #1: I2C Address (0x3C → 0x3D)
In `src/test_with_ml.cpp`, line ~54:
```cpp
if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {  // Changed from 0x3C
```

### Fix #2: Add Contrast Adjustment
In `setup()` function after `display.begin()`:
```cpp
display.setContrast(128);  // Scale 0-255, try 128 if too dim
```

### Fix #3: Add Text Scaling Fallback
If text is too small, in `displayStatus()`:
```cpp
display.setTextSize(2);  // Increase from 1 to 2
```

---

## **Verification Checklist**

After fixes, verify in this order:

- [ ] Serial Monitor shows no errors
- [ ] OLED displays text on startup ("ML Monitor Init...")
- [ ] Sensor values appear on screen
- [ ] Status line shows HEALTHY/CREEP/CAUTION
- [ ] Values update every ~500ms (smooth refresh)
- [ ] All 4 sensor readings visible (Noz, Bed, Curr, Vib)

---

## **If Still Not Working**

Try this minimal test code:

```cpp
#include <Wire.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void setup() {
  Serial.begin(9600);
  delay(1000);
  
  Serial.println("Wire.begin()...");
  Wire.begin();
  
  Serial.println("display.begin(0x3C)...");
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("FAILED at 0x3C, trying 0x3D...");
    display.begin(SSD1306_SWITCHCAPVCC, 0x3D);
  }
  
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("TEST");
  display.display();
  
  Serial.println("Done!");
}

void loop() {}
```

---

## **Last Resort: Hardware Check**

Use a multimeter to verify:
1. **SDA line**: Should be ~2.5V at rest
2. **SCL line**: Should be ~2.5V at rest
3. **VCC**: Should be 5V on OLED
4. **GND**: Should be 0V

If voltages are wrong, check for:
- Short circuits
- Broken wires
- Bad USB power

---

## **Getting Help**

When asking for help, provide:
1. Serial Monitor output (copy/paste exact text)
2. Photo of wiring connections
3. OLED module model/address if visible
4. Arduino board type confirmation

---

**Next: Run diagnostic, find your I2C address, update code, and verify display works! 🎯**
