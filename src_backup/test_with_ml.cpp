#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// DHT Sensors (Nozzle and Bed)
#define DHTPIN1 8
#define DHTPIN2 9
#define DHTTYPE DHT11
DHT dht1(DHTPIN1, DHTTYPE);
DHT dht2(DHTPIN2, DHTTYPE);

// Vibration Sensor
#define VIB_PIN 7
int vibCount = 0;
int lastState = LOW;
unsigned long startTime = 0;

// ACS712 Current Sensor
#define ACS_PIN A0
float sensitivity = 0.185;   // 5A module (change to 0.100 for 20A, 0.066 for 30A)
float zeroVoltage = 2.5;     // Adjust through calibration

// ==================== ML MODEL PARAMETERS ====================
// Normalized mean values (from scaler)
const float norm_mean[4] = {211.15, 61.59, 2.345, 95.05};

// Normalized std values (from scaler)  
const float norm_std[4] = {10.5, 5.8, 0.95, 12.2};

// Simple Rule-based Classification (Arduino-friendly)
// Using thresholds derived from data
const float HEALTHY_NOZZLE_MAX = 225.0;
const float CREEP_NOZZLE_MIN = 235.0;
const float HEALTHY_BED_MAX = 70.0;
const float CREEP_BED_MIN = 72.0;
const float HEALTHY_CURRENT_MAX = 1.8;
const float CREEP_CURRENT_MIN = 2.5;
const float HEALTHY_VIB_MAX = 70;
const float CREEP_VIB_MIN = 90;

// ==================== FUNCTION DECLARATIONS ====================
String classifyHealth(float nozzleTemp, float bedTemp, float motorCurrent, float vibPerMin);
void displayStatus(float nozzleTemp, float bedTemp, float motorCurrent, float vibPerMin, String status);

void setup() {
  Serial.begin(9600);
  
  pinMode(VIB_PIN, INPUT);
  
  dht1.begin();
  dht2.begin();

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    while (1) {
      Serial.println("OLED init failed!");
      delay(1000);
    }
  }

  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("ML Monitor Init...");
  display.display();
  
  startTime = millis();
  delay(2000);
}

void loop() {
  // ---------- Read Temperature ----------
  float nozzleTemp = dht1.readTemperature();
  float bedTemp = dht2.readTemperature();

  // ---------- Count Vibrations ----------
  int currentState = digitalRead(VIB_PIN);
  if (currentState == HIGH && lastState == LOW) {
    vibCount++;
  }
  lastState = currentState;

  // Reset vibration count every minute
  if (millis() - startTime >= 60000) {
    vibCount = 0;
    startTime = millis();
  }

  // ---------- Read Current ----------
  int rawCurrent = analogRead(ACS_PIN);
  float voltage = rawCurrent * (5.0 / 1023.0);
  float motorCurrent = (voltage - zeroVoltage) / sensitivity;

  // Handle sensor errors
  if (isnan(nozzleTemp) || isnan(bedTemp)) {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Sensor Error!");
    display.display();
    delay(500);
    return;
  }

  // ---------- ML Classification ----------
  String health_status = classifyHealth(nozzleTemp, bedTemp, motorCurrent, vibCount);

  // ---------- Display Results ----------
  displayStatus(nozzleTemp, bedTemp, motorCurrent, vibCount, health_status);

  // ---------- Serial Debug Output ----------
  Serial.print("Temp(N/B): ");
  Serial.print(nozzleTemp); Serial.print("/");
  Serial.print(bedTemp); Serial.print(" | ");
  Serial.print("Curr: ");
  Serial.print(motorCurrent); Serial.print("A | ");
  Serial.print("Vib: ");
  Serial.print(vibCount); Serial.print("/min | ");
  Serial.println("Status: " + health_status);

  delay(500);
}

// ==================== CLASSIFICATION FUNCTION ====================
String classifyHealth(float nozzleTemp, float bedTemp, float motorCurrent, float vibPerMin) {
  
  int healthy_score = 0;
  int creep_score = 0;

  // Score based on each parameter
  if (nozzleTemp < HEALTHY_NOZZLE_MAX) healthy_score++;
  if (nozzleTemp > CREEP_NOZZLE_MIN) creep_score++;

  if (bedTemp < HEALTHY_BED_MAX) healthy_score++;
  if (bedTemp > CREEP_BED_MIN) creep_score++;

  if (motorCurrent < HEALTHY_CURRENT_MAX) healthy_score++;
  if (motorCurrent > CREEP_CURRENT_MIN) creep_score++;

  if (vibPerMin < HEALTHY_VIB_MAX) healthy_score++;
  if (vibPerMin > CREEP_VIB_MIN) creep_score++;

  // Decision logic
  if (creep_score >= 3) {
    return "CREEP";
  } else if (healthy_score >= 3) {
    return "HEALTHY";
  } else {
    return "CAUTION";
  }
}

// ==================== DISPLAY FUNCTION ====================
void displayStatus(float nozzleTemp, float bedTemp, float motorCurrent, float vibPerMin, String status) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);

  // Row 1: Status (Large and Bold)
  display.setTextSize(2);
  display.setCursor(20, 0);
  if (status == "HEALTHY") {
    display.println("HEALTHY");
  } else if (status == "CREEP") {
    display.println("CREEP!");
  } else {
    display.println("CAUTION");
  }

  // Row 2-5: Sensor values (Small)
  display.setTextSize(1);
  display.setCursor(0, 20);
  
  display.print("Noz: ");
  display.print(nozzleTemp, 1);
  display.println("C");

  display.print("Bed: ");
  display.print(bedTemp, 1);
  display.println("C");

  display.print("Curr: ");
  display.print(motorCurrent, 2);
  display.println("A");

  display.print("Vib: ");
  display.print((int)vibPerMin);
  display.println("/min");

  display.display();
}
