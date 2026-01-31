#include <Arduino_RouterBridge.h>
#include <Modulino.h>
#include <Servo.h>
#include <NewPing.h>

const int trigPin = 8;
const int echoPin = 9;
const int left_wheel = 11;
const int right_wheel = 10;

const int greenPin = 1;
const int redPin = 2;
const int bluePin = 0;

const int arm1Pin = 3;
const int arm2Pin = 5;

Servo right_servo;
Servo left_servo;
Servo arm1_servo;
Servo arm2_servo;
ModulinoThermo thermo;
NewPing sonar(trigPin, echoPin, 1000);

int currentArm1Angle = 0;
int currentArm2Angle = 180;

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

    digitalWrite(bluePin, (b > 128) ? HIGH : LOW);
    digitalWrite(redPin, (r > 128) ? HIGH : LOW);
    digitalWrite(greenPin, (g > 128) ? HIGH : LOW);
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
    if (getDistance() > 25)
    {
        right_servo.write(90 - speed);
        left_servo.write(90 + speed);
    }
    else
    {
        Bridge.notify("play_random_sound", 0);
        right_servo.write(90 + speed);
        left_servo.write(90 - speed);
        delay(2000);
        right_servo.write(90 - speed);
        left_servo.write(90 - speed);
        delay(1000);
    }
}

void setArm1(int targetAngle)
{
    arm1_servo.write(targetAngle);
}
 

void setArm2(int targetAngle)
{
    arm2_servo.write(targetAngle);
}

void setup()
{
    Bridge.begin();
    Modulino.begin(Wire1);
    thermo.begin();

    Bridge.provide_safe("getDistance", getDistance);
    Bridge.provide_safe("setRGB", setRGB);
    Bridge.provide_safe("move", move);
    Bridge.provide_safe("panic", panic);
    Bridge.provide_safe("setArm1", setArm1);
    Bridge.provide_safe("setArm2", setArm2);

    pinMode(right_wheel, OUTPUT);
    pinMode(left_wheel, OUTPUT);
    right_servo.attach(right_wheel);
    left_servo.attach(left_wheel);

    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);
    pinMode(redPin, OUTPUT);
    pinMode(greenPin, OUTPUT);
    pinMode(bluePin, OUTPUT);

    pinMode(arm1Pin, OUTPUT);
    pinMode(arm2Pin, OUTPUT);
    arm1_servo.attach(arm1Pin);
    arm2_servo.attach(arm2Pin);

    // Make rainbow two times
    for (int i = 0; i < 2; i++)
    {
        digitalWrite(redPin, HIGH);
        digitalWrite(greenPin, LOW);
        digitalWrite(bluePin, LOW);
        
        delay(100);
        digitalWrite(redPin, HIGH);
        digitalWrite(greenPin, LOW);
        digitalWrite(bluePin, 130);
        
        delay(100);
        digitalWrite(redPin, HIGH);
        digitalWrite(greenPin, HIGH);
        digitalWrite(bluePin, LOW);
        delay(100);

        digitalWrite(redPin, LOW);
        digitalWrite(greenPin, HIGH);
        digitalWrite(bluePin, LOW);
        delay(100);
        
        digitalWrite(redPin, LOW);
        digitalWrite(greenPin, LOW);
        digitalWrite(bluePin, HIGH);
        delay(100);
        
        digitalWrite(redPin, LOW);
        digitalWrite(greenPin, LOW);
        digitalWrite(bluePin, HIGH);
        delay(100);

        digitalWrite(redPin, HIGH);
        digitalWrite(greenPin, LOW);
        digitalWrite(bluePin, HIGH);
        delay(100);
    }
}

void loop()
{
    static unsigned long lastTelemetryTime = 0;

    if (millis() - lastTelemetryTime >= 1000)
    {
        lastTelemetryTime = millis();

        float distance = sonar.ping_cm();
        Bridge.notify("set_distance", distance);

        float temperature = thermo.getTemperature();
        Bridge.notify("set_temperature", temperature);

        float humidity = thermo.getHumidity();
        Bridge.notify("set_humidity", humidity);
    }
}
