#include <Arduino_RouterBridge.h>

#include "ArduinoGraphics.h"
#include "Arduino_LED_Matrix.h"

#include <Modulino.h>
#include <Servo.h>
#include <NewPing.h>

Arduino_LED_Matrix matrix;

Servo right_servo;
Servo left_servo;

ModulinoThermo thermo;

const int trigPin = 8;
const int echoPin = 9;
const int left_wheel = 11;
const int right_wheel = 10;

NewPing sonar(trigPin, echoPin, 1000);

int speed = 0;  //0..90
int previousSpeed = 0;
int manual_speed = 45;

boolean back = false;
boolean left = false;
boolean right = false;
boolean forward = false;

float duration, distance = 100;

void setup() {
  Bridge.begin();
  Monitor.begin();
  
  Modulino.begin(Wire1);
  thermo.begin();

  pinMode(right_wheel, OUTPUT);
  pinMode(left_wheel, OUTPUT);
  right_servo.attach(right_wheel);
  left_servo.attach(left_wheel);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  matrix.begin();
  matrix.textFont(Font_5x7);
  matrix.textScrollSpeed(100);
  matrix.clear();
}

void loop() {
  Bridge.call("get_speed").result(speed);
  Bridge.call("get_back").result(back);
  Bridge.call("get_left").result(left);
  Bridge.call("get_right").result(right);
  Bridge.call("get_forward").result(forward);
  
  distance = sonar.ping_cm();
  Bridge.call("set_distance", distance);
  
//   matrix.beginText(0, 1, 127, 0, 0); // X, Y, then R, G, B
//   matrix.print(" distance=" + String(distance) + "  ");
//   matrix.endText(SCROLL_LEFT);

  float temperature = thermo.getTemperature();
  Bridge.call("set_temperature", temperature);
  
  float humidity = thermo.getHumidity();
  Bridge.call("set_humidity", humidity);

  if (left) {
    right_servo.write(90 - manual_speed);
    left_servo.write(90 - manual_speed);
    delay(1000);
  } else if (right) {
    right_servo.write(90 + manual_speed);
    left_servo.write(90 + manual_speed);
    delay(1000);
  } else if (forward) {
    right_servo.write(90 - manual_speed);
    left_servo.write(90 + manual_speed);
    delay(1000);
  } else if (back) {
    right_servo.write(90 + manual_speed);
    left_servo.write(90 - manual_speed);
    delay(1000);    
  } else if (distance > 25 || distance == 0 ) {
      right_servo.write(90 - speed);
      left_servo.write(90 + speed);
  } else {
    Bridge.call("speak", "Обнаружено препятствие");    
    right_servo.write(90 + speed);
    left_servo.write(90 - speed);
    delay(2000);
    right_servo.write(90 - speed);
    left_servo.write(90 - speed);
    delay(1000);
  }
  previousSpeed = speed;
  
  delay(200);
}
