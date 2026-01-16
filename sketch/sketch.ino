#include <Arduino_RouterBridge.h>
#include <Modulino.h>
#include <Servo.h>
#include <NewPing.h>

Servo right_servo;
Servo left_servo;

ModulinoThermo thermo;
NewPing sonar(trigPin, echoPin, 1000);

const int trigPin = 8;
const int echoPin = 9;
const int left_wheel = 11;
const int right_wheel = 10;

const int redPin = 3;
const int greenPin = 5;
const int bluePin = 6;

float getDistance()
{
    float d = sonar.ping_cm();
    if (d == 0)
        d = 1000;
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

    Monitor.print("Executing move cmd: ");
    Monitor.println(mvcmd);

    // expected formats:
    // MOVE|forward|20|45  -> direction, distance_cm, speed
    // TURN|left|45|45    -> direction, angle_deg, speed
    // STOP
    int idx1 = mvcmd.indexOf('|');
    String verb = mvcmd;
    if (idx1 != -1)
        verb = mvcmd.substring(0, idx1);

    if (verb == "MOVE")
    {
        // parse parts
        int p1 = mvcmd.indexOf('|', idx1 + 1);
        int p2 = mvcmd.indexOf('|', p1 + 1);
        String dir = mvcmd.substring(idx1 + 1, p1);
        String distStr = mvcmd.substring(p1 + 1, p2);
        String spdStr = mvcmd.substring(p2 + 1);
        int dist = distStr.toInt();
        int mvspd = spdStr.toInt();
        Monitor.print("MOVE verb parsed: ");
        Monitor.print(dir);
        Monitor.print(" dist=");
        Monitor.print(dist);
        Monitor.print(" spd=");
        Monitor.println(mvspd);

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
            delay(ms);
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
        Monitor.print("AGI TURN verb parsed: ");
        Monitor.print(dir);
        Monitor.print(" ang=");
        Monitor.print(ang);
        Monitor.print(" spd=");
        Monitor.println(mvspd);

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
        Monitor.println("AGI STOP\n");
        right_servo.write(90);
        left_servo.write(90);
    }
}

void setup()
{
    Bridge.begin();
    Monitor.begin();

    Modulino.begin(Wire1);
    thermo.begin();

    Bridge.provide("getDistance", getDistance);
    Bridge.provide("setRGB", setRGB);
    Bridge.provide("move", move);

    pinMode(right_wheel, OUTPUT);
    pinMode(left_wheel, OUTPUT);
    right_servo.attach(right_wheel);
    left_servo.attach(left_wheel);
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);

    // Flash red and blue for 5 seconds
    for (int i = 0; i < 25; i++)
    {
        analogWrite(redPin, 255);
        analogWrite(bluePin, 0);
        analogWrite(greenPin, 0);
        delay(100);
        analogWrite(redPin, 0);
        analogWrite(bluePin, 255);
        analogWrite(greenPin, 0);
        delay(100);
    }
}

unsigned long previousMillis = 0UL;
unsigned long interval = 1000UL;

void loop()
{
    unsigned long currentMillis = millis();

    if (currentMillis - previousMillis > interval)
    {
        distance = sonar.ping_cm();
        Bridge.call("set_distance", distance);

        float temperature = thermo.getTemperature();
        Bridge.call("set_temperature", temperature);

        float humidity = thermo.getHumidity();
        Bridge.call("set_humidity", humidity);

        previousMillis = currentMillis;
    }
}
