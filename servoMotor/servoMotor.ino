#include <Servo.h>

const int trigPin = 10;
const int echoPin = 11;
const int greenLED = 8;
const int redLED = 9;
Servo gateServo;

int restingAngle = 90;
int openAngle = 20;    // change to your gate open angle
int closeAngle = 90;

long readDistanceCm() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000); // 30ms timeout
  if (duration == 0) return 999; // no echo
  float distance = duration * 0.034 / 2.0;
  return (long)distance;
}

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(redLED, OUTPUT);
  gateServo.attach(12);
  gateServo.write(restingAngle);
  digitalWrite(greenLED, HIGH);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "START_TAP") {
      digitalWrite(redLED, HIGH);
      digitalWrite(greenLED, LOW);
      int taps = detectTaps(5000); // 5000 ms window
      Serial.print("TAPS:");
      Serial.println(taps);
      digitalWrite(redLED, LOW);
      digitalWrite(greenLED, HIGH);
    } 
    else if (command == "OPEN") {
      gateServo.write(openAngle);
      Serial.println("STATUS:OPENED");
    }
    else if (command == "CLOSE") {
      gateServo.write(closeAngle);
      Serial.println("STATUS:CLOSED");
    }
  }
}

// Detect taps by watching for quick proximity events.
// Returns count of taps detected within window_ms.
int detectTaps(unsigned long window_ms) {
  unsigned long start = millis();
  int taps = 0;
  bool inProx = false;
  const int proxThreshold = 15; // cm - treat <15cm as proximity/tap; tune this
  const int minDebounceMs = 150; // minimum ms between counted taps

  unsigned long lastTapTime = 0;

  while (millis() - start < window_ms) {
    long d = readDistanceCm();
    unsigned long now = millis();

    if (d < proxThreshold) {
      if (!inProx && (now - lastTapTime > minDebounceMs)) {
        // new tap
        taps++;
        inProx = true;
        lastTapTime = now;
      } else {
        inProx = true;
      }
    } else {
      // not prox
      inProx = false;
    }
  }
  return taps;
}
