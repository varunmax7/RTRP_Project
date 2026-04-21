#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

// Try both addresses
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void setup() {
  Serial.begin(9600);
  delay(1000);
  
  Serial.println("Starting OLED Simple Test...");
  
  // Initialize I2C
  Wire.begin();
  
  // Try address 0x3C first
  Serial.print("Trying address 0x3C... ");
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SUCCESS!");
  } else {
    Serial.println("FAILED - trying 0x3D...");
    // Reinitialize for 0x3D
    Adafruit_SSD1306 display2(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
    if (display2.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {
      Serial.println("SUCCESS at 0x3D!");
    } else {
      Serial.println("FAILED at both addresses!");
      Serial.println("Check your OLED wiring:");
      Serial.println("  SDA -> A4 (or marked SDA)");
      Serial.println("  SCL -> A5 (or marked SCL)");
      Serial.println("  VCC -> 5V");
      Serial.println("  GND -> GND");
      while(1) {
        delay(1000);
      }
    }
  }
  
  // Clear and test
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("OLED TEST");
  display.println("========");
  display.println("If you see this,");
  display.println("OLED is working!");
  display.display();
  
  Serial.println("If you see text on OLED, it's working!");
}

void loop() {
  delay(100);
}
