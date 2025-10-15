#include <Servo.h>

const int trigPin = 10;
const int echoPin = 11;
const int greenLED = 8;
const int redLED = 9;

Servo myServo;

int angle = 90;          // starting/resting position
int step = 1;            // servo step
bool scanning = false;   // is object detected?

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(redLED, OUTPUT);

  myServo.attach(12);
  myServo.write(angle);
  digitalWrite(greenLED, HIGH);
}

void loop() {
  float distance = getDistance();
  Serial.println(distance);

  if (distance <= 10) {
    // Object detected
    scanning = true;
    digitalWrite(redLED, HIGH);
    digitalWrite(greenLED, LOW);

    angle += step;           // move servo gradually
    if (angle >= 165 || angle <= 15) step = -step; // reverse direction at limits
    myServo.write(angle);
    delay(20);               // short delay for smooth motion
  } 
  else {
    // No object
    scanning = false;
    digitalWrite(redLED, LOW);
    digitalWrite(greenLED, HIGH);

    // Return servo to resting position
    if (angle != 90) {
      if (angle < 90) angle++;
      else if (angle > 90) angle--;
      myServo.write(angle);
      delay(15);
    }
  }
}

float getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2; // distance in cm
  return distance;
}
