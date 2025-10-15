#include <Servo.h>
const int trigPin = 10;
const int echoPin = 11;
const int greenLED = 8;   // :white_check_mark: Green LED (open)
const int redLED = 9;     // :white_check_mark: Red LED (closed)
const int servoPin = 12;
Servo gateServo;
// --- Configuration ---
int openAngle = 20;   // Adjust for your servo gate open position
int closeAngle = 90;  // Adjust for your servo closed position
int proxThreshold = 15;   // cm distance to count a tap
int debounceMs = 400;     // ms delay between taps
// --- Function: measure distance ---
long readDistanceCm() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH, 30000); // 30ms timeout
  if (duration == 0) return 999;
  return duration * 0.034 / 2;
}
// --- Function: tap detection ---
int detectTaps(unsigned long window_ms) {
  unsigned long start = millis();
  int taps = 0;
  bool tapActive = false;
  unsigned long lastTap = 0;
  while (millis() - start < window_ms) {
    long d = readDistanceCm();
    unsigned long now = millis();
    if (d < proxThreshold && !tapActive) {
      if (now - lastTap > debounceMs) {
        taps++;
        Serial.print("Tap detected #");
        Serial.println(taps);
        lastTap = now;
      }
      tapActive = true;
    }
    else if (d >= proxThreshold + 3) {
      tapActive = false;
    }
    delay(50);
  }
  return taps;
}
// --- Function: Gate Control ---
void openGate() {
  gateServo.write(openAngle);
  digitalWrite(greenLED, HIGH);
  digitalWrite(redLED, LOW);
  Serial.println("STATUS:OPENED");
}
void closeGate() {
  gateServo.write(closeAngle);
  digitalWrite(greenLED, LOW);
  digitalWrite(redLED, HIGH);
  Serial.println("STATUS:CLOSED");
}
// --- Setup ---
void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(redLED, OUTPUT);
  gateServo.attach(servoPin);
  closeGate(); // Start with gate closed (red ON)
  Serial.println("System ready");
}
// --- Loop ---
void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "START_TAP") {
      // Indicate tap detection mode
      digitalWrite(redLED, HIGH);
      digitalWrite(greenLED, LOW);
      int taps = detectTaps(5000);
      Serial.print("TAPS:");
      Serial.println(taps);
      // After tap detection, revert to closed state LED
      digitalWrite(redLED, HIGH);
      digitalWrite(greenLED, LOW);
    }
    else if (command == "OPEN") {
      openGate();
    }
    else if (command == "CLOSE") {
      closeGate();
    }
  }
}