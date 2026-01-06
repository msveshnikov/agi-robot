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

int speed = 45; // 0..90

boolean back = false;
boolean left = false;
boolean right = false;
boolean forward = false;
boolean agi = false;

float duration, distance;

void setup()
{
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

void loop()
{
    Bridge.call("get_speed").result(speed);
    Bridge.call("get_back").result(back);
    Bridge.call("get_left").result(left);
    Bridge.call("get_right").result(right);
    Bridge.call("get_forward").result(forward);
    Bridge.call("get_agi").result(agi);

    distance = sonar.ping_cm();
    Bridge.call("set_distance", distance);

    float temperature = thermo.getTemperature();
    Bridge.call("set_temperature", temperature);

    float humidity = thermo.getHumidity();
    Bridge.call("set_humidity", humidity);

    if (left)
    {
        right_servo.write(90 - speed);
        left_servo.write(90 - speed);
        delay(1000);
    }
    else if (right)
    {
        right_servo.write(90 + speed);
        left_servo.write(90 + speed);
        delay(1000);
    }
    else if (forward)
    {
        right_servo.write(90 - speed);
        left_servo.write(90 + speed);
        delay(1000);
    }
    else if (back)
    {
        right_servo.write(90 + speed);
        left_servo.write(90 - speed);
        delay(1000);
    }
    else if (agi)
    {
        Bridge.call("agi_loop");
    }
    else
    {
        right_servo.write(90);
        left_servo.write(90);
        delay(1000);
    }

    delay(200);
}
