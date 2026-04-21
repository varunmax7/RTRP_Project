#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// DHT Sensors
#define DHTPIN1 8
#define DHTPIN2 9
#define DHTTYPE DHT11
DHT dht1(DHTPIN1, DHTTYPE);
DHT dht2(DHTPIN2, DHTTYPE);

// Vibration Sensor
#define VIB_PIN 7
volatile int vibCount = 0;
int lastState = LOW;
unsigned long startTime = 0;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;  // 50ms debounce for noisy signals

// ACS712 Current Sensor
#define ACS_PIN A0
float sensitivity = 0.185;
float zeroVoltage = 2.5;

// ==================== HEALTH MODEL PARAMETERS ====================
// Threshold ranges for healthy and degraded states
const float NOZZLE_HEALTHY_MAX = 225.0;
const float NOZZLE_DEGRADE_MIN = 230.0;
const float NOZZLE_DEGRADE_MAX = 240.0;
const float NOZZLE_FAIL_MIN = 245.0;

const float BED_HEALTHY_MAX = 70.0;
const float BED_DEGRADE_MIN = 72.0;
const float BED_DEGRADE_MAX = 80.0;
const float BED_FAIL_MIN = 85.0;

const float CURRENT_HEALTHY_MAX = 1.8;
const float CURRENT_DEGRADE_MIN = 2.0;
const float CURRENT_DEGRADE_MAX = 2.8;
const float CURRENT_FAIL_MIN = 3.2;

const float VIB_HEALTHY_MAX = 70;
const float VIB_DEGRADE_MIN = 75;
const float VIB_DEGRADE_MAX = 95;
const float VIB_FAIL_MIN = 110;

// ==================== STRUCTURES ====================
struct HealthMetrics {
  String status;           // "HEALTHY", "DEGRADING", "FAILING"
  int overallHealth;       // 0-100%
  int rul_hours;           // Remaining Useful Life in hours
  int nozzleHealth;        // 0-100%
  int bedHealth;           // 0-100%
  int motorHealth;         // 0-100%
  String action;           // Recommended action
  char icon;               // 'C', 'W', 'X'
};

// ==================== FUNCTION DECLARATIONS ====================
HealthMetrics calculateHealth(float nozzleTemp, float bedTemp, float motorCurrent, float vibPerMin);
int mapToHealth(float value, float healthy_max, float degrade_min, float degrade_max, float fail_min);
void displayAdvancedHealth(HealthMetrics metrics, float nozzleTemp, float bedTemp);

void setup() {
  Serial.begin(9600);
  delay(1000);
  
  pinMode(VIB_PIN, INPUT);
  dht1.begin();
  dht2.begin();

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED init failed!");
    while (1);
  }

  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("ML Health Monitor");
  display.println("Initializing...");
  display.display();
  
  startTime = millis();
  delay(2000);
}

void loop() {
  // Read sensors
  float nozzleTemp = dht1.readTemperature();
  float bedTemp = dht2.readTemperature();

  // Count vibrations with debouncing
  int currentState = digitalRead(VIB_PIN);
  
  // Debouncing logic
  if (currentState != lastState) {
    lastDebounceTime = millis();
  }
  
  // After debounce delay, if state is still different, record it
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (currentState == HIGH && lastState == LOW) {
      vibCount++;
    }
    lastState = currentState;
  }

  // Reset vibration count every minute
  if (millis() - startTime >= 60000) {
    vibCount = 0;
    startTime = millis();
  }

  // Read current
  int rawCurrent = analogRead(ACS_PIN);
  float voltage = rawCurrent * (5.0 / 1023.0);
  float motorCurrent = (voltage - zeroVoltage) / sensitivity;

  // Handle sensor errors
  if (isnan(nozzleTemp) || isnan(bedTemp)) {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Sensor Error!");
    display.display();
    delay(100);  // Reduced from 500 to capture more vibrations
    return;
  }

  // Calculate health metrics
  HealthMetrics metrics = calculateHealth(nozzleTemp, bedTemp, motorCurrent, vibCount);

  // Display results
  displayAdvancedHealth(metrics, nozzleTemp, bedTemp);

  // Detailed Serial debug output for live sensor data
  Serial.print(">>> LIVE DATA | ");
  Serial.print("Nozzle: ");
  Serial.print(nozzleTemp);
  Serial.print(" C | Bed: ");
  Serial.print(bedTemp);
  Serial.print(" C | Current: ");
  Serial.print(motorCurrent);
  Serial.print(" A | Vib: ");
  Serial.print(vibCount);
  Serial.println(" pulses/min");

  Serial.print("--- HEALTH | Status: ");
  Serial.print(metrics.status);
  Serial.print(" | Health: ");
  Serial.print(metrics.overallHealth);
  Serial.print("% | RUL: ");
  Serial.print(metrics.rul_hours);
  Serial.print("h | Action: ");
  Serial.println(metrics.action);
  Serial.println("---------------------------------------------------------");

  delay(100);  // Reduced from 500ms to capture more vibration events
}

// ==================== MAP VALUE TO HEALTH PERCENTAGE ====================
int mapToHealth(float value, float healthy_max, float degrade_min, float degrade_max, float fail_min) {
  if (value <= healthy_max) {
    return 100;  // Perfect health
  } else if (value >= fail_min) {
    return 10;   // Critical failure
  } else if (value >= degrade_max) {
    return map(value * 10, degrade_max * 10, fail_min * 10, 40, 20);  // Severe degradation
  } else if (value >= degrade_min) {
    return map(value * 10, degrade_min * 10, degrade_max * 10, 70, 40);  // Mild degradation
  }
  return 85;  // Between healthy and degrade zone
}

// ==================== CALCULATE HEALTH METRICS ====================
HealthMetrics calculateHealth(float nozzleTemp, float bedTemp, float motorCurrent, float vibPerMin) {
  HealthMetrics metrics;
  
  // Calculate individual component health scores
  metrics.nozzleHealth = mapToHealth(nozzleTemp, NOZZLE_HEALTHY_MAX, NOZZLE_DEGRADE_MIN, NOZZLE_DEGRADE_MAX, NOZZLE_FAIL_MIN);
  metrics.bedHealth = mapToHealth(bedTemp, BED_HEALTHY_MAX, BED_DEGRADE_MIN, BED_DEGRADE_MAX, BED_FAIL_MIN);
  metrics.motorHealth = mapToHealth(motorCurrent, CURRENT_HEALTHY_MAX, CURRENT_DEGRADE_MIN, CURRENT_DEGRADE_MAX, CURRENT_FAIL_MIN);
  
  int vibHealth = mapToHealth(vibPerMin, VIB_HEALTHY_MAX, VIB_DEGRADE_MIN, VIB_DEGRADE_MAX, VIB_FAIL_MIN);
  
  // Calculate overall health (average of all components)
  metrics.overallHealth = (metrics.nozzleHealth + metrics.bedHealth + metrics.motorHealth + vibHealth) / 4;
  
  // Determine status and icon
  if (metrics.overallHealth >= 80) {
    metrics.status = "HEALTHY";
    metrics.icon = 'C';  // Checkmark equivalent
    metrics.action = "CONTINUE";
    metrics.rul_hours = 48;
  } else if (metrics.overallHealth >= 60) {
    metrics.status = "DEGRADING";
    metrics.icon = 'W';  // Warning
    metrics.action = "MONITOR";
    metrics.rul_hours = 12;
  } else if (metrics.overallHealth >= 40) {
    metrics.status = "CAUTION";
    metrics.icon = 'W';
    metrics.action = "SERVICE SOON";
    metrics.rul_hours = 6;
  } else {
    metrics.status = "FAILING";
    metrics.icon = 'X';
    metrics.action = "STOP PRINTING";
    metrics.rul_hours = 1;
  }
  
  // Specific recommendations based on which sensor is worst
  int worst_component = 0;
  if (metrics.nozzleHealth < worst_component || worst_component == 0) {
    worst_component = metrics.nozzleHealth;
    if (metrics.nozzleHealth < 50) {
      metrics.action = "CLEAN NOZZLE";
      metrics.rul_hours = min(metrics.rul_hours, 6);
    }
  }
  if (metrics.motorHealth < worst_component) {
    worst_component = metrics.motorHealth;
    if (metrics.motorHealth < 50) {
      metrics.action = "CHECK MOTOR";
      metrics.rul_hours = min(metrics.rul_hours, 4);
    }
  }
  if (metrics.bedHealth < worst_component) {
    worst_component = metrics.bedHealth;
    if (metrics.bedHealth < 50) {
      metrics.action = "LEVEL BED";
      metrics.rul_hours = min(metrics.rul_hours, 6);
    }
  }
  
  return metrics;
}

// ==================== DISPLAY ADVANCED HEALTH ON OLED ====================
void displayAdvancedHealth(HealthMetrics metrics, float nozzleTemp, float bedTemp) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  
  // Line 1: STATUS
  display.setCursor(0, 0);
  display.print("ST: ");
  display.print(metrics.status);
  display.print(" ");
  display.print(metrics.overallHealth);
  display.println("%");

  // Line 2: Temperatures (Live Values) - Moved to be more visible
  display.setCursor(0, 12);
  display.print("NOZ:");
  display.print((int)nozzleTemp);
  display.print("C  BED:");
  display.print((int)bedTemp);
  display.println("C");
  
  // Line 3: RUL & Sub-health
  display.setCursor(0, 24);
  display.print("RUL:");
  display.print(metrics.rul_hours);
  display.print("h N:");
  display.print(metrics.nozzleHealth);
  display.println("%");

  // Line 4: More Sub-health
  display.setCursor(0, 36);
  display.print("M:");
  display.print(metrics.motorHealth);
  display.print("% B:");
  display.print(metrics.bedHealth);
  display.println("%");
  
  // Line 5: ACTION recommendation - Clear and at bottom
  display.setCursor(0, 50);
  display.print("-> ");
  display.println(metrics.action);
  
  display.display();
}
