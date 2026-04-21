// ABSOLUTE MINIMAL TEST - NO LIBRARIES
// This proves the board is working

#include <Arduino.h>

void setup() {
  // Initialize serial for debugging
  Serial.begin(9600);
  
  // Setup LED pin (built-in LED on Arduino Micro is pin 13)
  pinMode(13, OUTPUT);
  
  // Wait a moment
  delay(1000);
  
  // Send startup message
  Serial.println("======= BOARD ALIVE =======");
  Serial.println("If you see this, board is working!");
  Serial.println("============================");
  Serial.println("");
}

int counter = 0;

void loop() {
  // Blink LED
  digitalWrite(13, HIGH);
  delay(500);
  digitalWrite(13, LOW);
  delay(500);
  
  // Print to serial
  counter++;
  Serial.print("Loop #");
  Serial.println(counter);
}
