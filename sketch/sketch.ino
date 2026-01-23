#include <Arduino_RouterBridge.h>
#include <Modulino.h>
#include <Servo.h>
#include <NewPing.h>

const int trigPin = 8;
const int echoPin = 9;
const int left_wheel = 11;
const int right_wheel = 10;

const int redPin = 3;
const int greenPin = 5;
const int bluePin = 6;

Servo right_servo;
Servo left_servo;
ModulinoThermo thermo;
NewPing sonar(trigPin, echoPin, 1000);

float getDistance()
{
    float d = sonar.ping_cm();
    if (d == 0)
    {
        d = 1000;
    }
    return d;
}

void setRGB(String rgb_str)
{
    int r = 0, g = 0, b = 0;
    int firstComma = rgb_str.indexOf(',');
    int secondComma = rgb_str.indexOf(',', firstComma + 1);

    if (firstComma != -1 && secondComma != -1)
    {
        r = rgb_str.substring(0, firstComma).toInt();
        g = rgb_str.substring(firstComma + 1, secondComma).toInt();
        b = rgb_str.substring(secondComma + 1).toInt();
    }

    analogWrite(bluePin, b);
    analogWrite(redPin, r / 1.2);
    analogWrite(greenPin, g / 2);
}

void move(String mvcmd, boolean stop)
{
    if (mvcmd.length() == 0)
        return;
    int idx1 = mvcmd.indexOf('|');
    String verb = mvcmd;
    if (idx1 != -1)
        verb = mvcmd.substring(0, idx1);

    if (verb == "MOVE")
    {
        int p1 = mvcmd.indexOf('|', idx1 + 1);
        int p2 = mvcmd.indexOf('|', p1 + 1);
        String dir = mvcmd.substring(idx1 + 1, p1);
        String distStr = mvcmd.substring(p1 + 1, p2);
        String spdStr = mvcmd.substring(p2 + 1);
        int dist = distStr.toInt();
        int mvspd = spdStr.toInt();
        // estimate time by speed
        float base_cm_per_sec = 20.0; // at speed ~45
        float cm_per_sec = base_cm_per_sec * ((mvspd > 0) ? ((float)mvspd / 45.0) : 1.0);
        if (cm_per_sec < 0.5)
            cm_per_sec = 0.5;
        unsigned long ms = (unsigned long)((dist / cm_per_sec) * 1000.0);

        if (dir == "forward")
        {
            right_servo.write(90 - mvspd);
            left_servo.write(90 + mvspd);
            unsigned long startTime = millis();
            while (millis() - startTime < ms)
            {
                if (getDistance() < 10)
                {
                    right_servo.write(90);
                    left_servo.write(90);
                    break;
                }
                delay(50);
            }
        }
        else if (dir == "back")
        {
            right_servo.write(90 + mvspd);
            left_servo.write(90 - mvspd);
            delay(ms);
        }
        if (stop)
        {
            right_servo.write(90);
            left_servo.write(90);
        }
    }
    else if (verb == "TURN")
    {
        int p1 = mvcmd.indexOf('|', idx1 + 1);
        int p2 = mvcmd.indexOf('|', p1 + 1);
        String dir = mvcmd.substring(idx1 + 1, p1);
        String angStr = mvcmd.substring(p1 + 1, p2);
        String spdStr = mvcmd.substring(p2 + 1);
        int ang = angStr.toInt();
        int mvspd = spdStr.toInt();

        // estimate ms per degree
        float ms_per_deg_base = 40.0; // empirical base at speed 45
        float scale = (mvspd > 0) ? ((float)mvspd / 45.0) : 1.0;
        unsigned long ms = (unsigned long)(ang * ms_per_deg_base / scale);

        if (dir == "left")
        {
            right_servo.write(90 - mvspd);
            left_servo.write(90 - mvspd);
            delay(ms);
        }
        else if (dir == "right")
        {
            right_servo.write(90 + mvspd);
            left_servo.write(90 + mvspd);
            delay(ms);
        }
        if (stop)
        {
            right_servo.write(90);
            left_servo.write(90);
        }
    }
    else if (verb == "STOP")
    {
        right_servo.write(90);
        left_servo.write(90);
    }
} 

void panic(int speed)
{
  if (getDistance() > 25) {
    right_servo.write(90 - speed);
    left_servo.write(90 + speed);
  } else {
    Bridge.notify("play_panic_sound", 0);
    right_servo.write(90 + speed);
    left_servo.write(90 - speed);
    delay(2000);
    right_servo.write(90 - speed);
    left_servo.write(90 - speed);
    delay(1000);
  }
}

void setup()
{
    Bridge.begin();
    Modulino.begin(Wire1);
    thermo.begin();

    Bridge.provide("getDistance", getDistance);
    Bridge.provide("setRGB", setRGB);
    Bridge.provide("move", move);
    Bridge.provide("panic", panic);

    pinMode(right_wheel, OUTPUT);
    pinMode(left_wheel, OUTPUT);
    right_servo.attach(right_wheel);
    left_servo.attach(left_wheel);
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);

    // Make rainbow two times
    for (int i = 0; i < 2; i++)
    {
        analogWrite(redPin, 255); analogWrite(greenPin, 0); analogWrite(bluePin, 0); delay(100);
        analogWrite(redPin, 255); analogWrite(greenPin, 127); analogWrite(bluePin, 0); delay(100);
        analogWrite(redPin, 255); analogWrite(greenPin, 255); analogWrite(bluePin, 0); delay(100);
        analogWrite(redPin, 0); analogWrite(greenPin, 255); analogWrite(bluePin, 0); delay(100);
        analogWrite(redPin, 0); analogWrite(greenPin, 0); analogWrite(bluePin, 255); delay(100);
        analogWrite(redPin, 75); analogWrite(greenPin, 0); analogWrite(bluePin, 130); delay(100);
        analogWrite(redPin, 143); analogWrite(greenPin, 0); analogWrite(bluePin, 255); delay(100);
    }
}

void loop()
{
    float distance = sonar.ping_cm();
    Bridge.notify("set_distance", distance);

    float temperature = thermo.getTemperature();
    Bridge.notify("set_temperature", temperature);

    float humidity = thermo.getHumidity();
    Bridge.notify("set_humidity", humidity);

    delay(1000);
}
