#include <Arduino_RouterBridge.h>
#include <Modulino.h>
#include <Servo.h>
#include <NewPing.h>

const int trigPin = 8;
const int echoPin = 9;
const int left_wheel = 11;
const int right_wheel = 10;

const int redPin = 5;
const int greenPin = 6;
const int bluePin = 3;

const int arm1Pin = 4;
const int arm2Pin = 7;

Servo right_servo;
Servo left_servo;
Servo arm1_servo;
Servo arm2_servo;
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
                // NOVA: eyes sit 9 cm ahead of the body centre; the claw reaches
                // ~3-5 cm in front of them, so allow close approaches (HC-SR04 min ~2-3 cm)
                if (getDistance() < 4)
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

void panic(String speedStr)
{
    int speed = speedStr.toInt();
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

// ---------------------------------------------------------------------------
// Manipulator (NOVA shell): arm1 = shoulder, arm2 = elbow
//   arm1: 0 = folded back into the roof bay, 90 = straight up, 180 = forward
//   arm2: 180 = straight, 90 = right angle (points at the floor when arm1=180)
// Moves are interpolated with an ease-in-out profile so the 9 g servos do not
// jerk the light chassis (and do not brown-out the USB power bank).
// ---------------------------------------------------------------------------
const int ARM1_MIN = 0, ARM1_MAX = 180;
const int ARM2_MIN = 20, ARM2_MAX = 180;   // < 20 the forearm hits the upper arm
int arm1_pos = 0;
int arm2_pos = 180;

int clampInt(int v, int lo, int hi)
{
    return v < lo ? lo : (v > hi ? hi : v);
}

// Smoothly move both joints to (a1, a2) in roughly `ms` milliseconds.
void armTo(int a1, int a2, int ms)
{
    a1 = clampInt(a1, ARM1_MIN, ARM1_MAX);
    a2 = clampInt(a2, ARM2_MIN, ARM2_MAX);
    int d = max(abs(a1 - arm1_pos), abs(a2 - arm2_pos));
    if (ms <= 0)
        ms = d * 8; // default ~125 deg/s
    ms = clampInt(ms, 0, 4000);
    int steps = max(1, ms / 15);
    int s1 = arm1_pos, s2 = arm2_pos;
    for (int i = 1; i <= steps; i++)
    {
        float t = (float)i / steps;
        float e = t * t * (3.0 - 2.0 * t); // smoothstep
        arm1_servo.write(s1 + (int)((a1 - s1) * e));
        arm2_servo.write(s2 + (int)((a2 - s2) * e));
        delay(15);
    }
    arm1_pos = a1;
    arm2_pos = a2;
}

// "a1,a2,ms" - used by the Python arm skills layer
void armPose(String pose)
{
    int c1 = pose.indexOf(',');
    int c2 = pose.indexOf(',', c1 + 1);
    if (c1 < 0)
        return;
    int a1 = pose.substring(0, c1).toInt();
    int a2 = (c2 < 0) ? pose.substring(c1 + 1).toInt() : pose.substring(c1 + 1, c2).toInt();
    int ms = (c2 < 0) ? 0 : pose.substring(c2 + 1).toInt();
    armTo(a1, a2, ms);
}

void setArm1(int targetAngle)
{
    armTo(targetAngle, arm2_pos, 0);
}

void setArm2(int targetAngle)
{
    armTo(arm1_pos, targetAngle, 0);
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
    Bridge.provide("setArm1", setArm1);
    Bridge.provide("setArm2", setArm2);
    Bridge.provide("armPose", armPose);

    pinMode(right_wheel, OUTPUT);
    pinMode(left_wheel, OUTPUT);
    right_servo.attach(right_wheel);
    left_servo.attach(left_wheel);

    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);

    pinMode(arm1Pin, OUTPUT);
    pinMode(arm2Pin, OUTPUT);
    arm1_servo.attach(arm1Pin);
    arm2_servo.attach(arm2Pin);
    arm1_servo.write(arm1_pos); // start parked in the roof bay
    arm2_servo.write(arm2_pos);

    // Make rainbow two times using setRGB
    for (int i = 0; i < 2; i++)
    {
        setRGB("255,0,0");
        delay(100);

        setRGB("255,0,130");
        delay(100);

        setRGB("255,255,0");
        delay(100);

        setRGB("0,255,0");
        delay(100);

        setRGB("0,0,255");
        delay(100);

        setRGB("0,0,255");
        delay(100);

        setRGB("255,0,255");
        delay(100);
    }
}

void loop()
{
    static unsigned long lastTelemetryTime = 0;

    if (millis() - lastTelemetryTime >= 3000)
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
