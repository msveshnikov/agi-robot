#include <Arduino_RouterBridge.h>

#include <Servo.h>
#include <NewPing.h>

Servo right_servo;
Servo left_servo;

const int trigPin = 8;
const int echoPin = 9;
const int left_wheel = 11;
const int right_wheel = 10;

NewPing sonar(trigPin, echoPin, 1000);

int speed = 0;  //0..90

float duration, distance = 100;

void setup() {
  Bridge.begin();
  pinMode(right_wheel, OUTPUT);
  pinMode(left_wheel, OUTPUT);
  right_servo.attach(right_wheel);
  left_servo.attach(left_wheel);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  Bridge.call("get_speed").result(speed);
  // if (speed == 0) {
  //   return;
  // }
  distance = sonar.ping_cm();
  if (distance > 25) {
    right_servo.write(90 - speed);
    left_servo.write(90 + speed);
  } else {
    right_servo.write(90 + speed);
    left_servo.write(90 - speed);
    delay(2000);
    right_servo.write(90 - speed);
    left_servo.write(90 - speed);
    delay(1000);
  }

  delay(200);
}
