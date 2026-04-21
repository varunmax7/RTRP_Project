#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void scanI2C();

void setup() {
  Serial.begin(9600);
  delay(2000);
  
  Serial.println("\n=== OLED DIAGNOSTIC TEST ===\n");
  
  // Step 1: Test I2C communication
  Serial.println("Step 1: Scanning I2C addresses...");
  scanI2C();
  
  // Step 2: Try to initialize display at 0x3C
  Serial.println("\nStep 2: Initializing display at 0x3C...");
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("ERROR: Display not found at 0x3C!");
    Serial.println("Trying to initialize at 0x3D...");
    
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {
      Serial.println("ERROR: Display not found at 0x3D either!");
      Serial.println("\nPossible causes:");
      Serial.println("1. Check SDA/SCL wiring");
      Serial.println("2. Verify 3.3V or 5V power to display");
      Serial.println("3. Ensure pull-up resistors on SDA/SCL");
      Serial.println("4. Try I2C Scanner sketch to find address");
      while(1) delay(1000);
    } else {
      Serial.println("SUCCESS: Display found at 0x3D!");
      Serial.println("UPDATE CODE: Change 0x3C to 0x3D");
    }
  } else {
    Serial.println("SUCCESS: Display initialized at 0x3C!");
  }
  
  // Step 3: Test display output
  Serial.println("\nStep 3: Testing display output...");
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("OLED OK!");
  display.println("Address:");
  display.setTextSize(1);
  display.println("0x3C");
  display.display();
  
  Serial.println("OLED should now show 'OLED OK!'");
  Serial.println("\nAll diagnostics complete!");
}

void loop() {
  delay(1000);
}

void scanI2C() {
  byte error, address;
  int nDevices = 0;
  
  Serial.println("Scanning...");
  
  for(address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      Serial.println(" (decimal: " + String(address) + ")");
      nDevices++;
      
      if (address == 0x3C || address == 0x3D) {
        Serial.println("  ^ This looks like your OLED display!");
      }
    }
  }
  
  if (nDevices == 0) {
    Serial.println("No I2C devices found!");
    Serial.println("Check wiring! SDA and SCL must be connected.");
  }
}
