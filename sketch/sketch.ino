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

const int redPin = 6;
const int greenPin = 5;
const int bluePin = 3;

String rgb_str = "0,0,0";

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

    pinMode(redPin, OUTPUT);
    pinMode(greenPin, OUTPUT);
    pinMode(bluePin, OUTPUT);

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

    Bridge.call("get_rgb").result(rgb_str);

    // Parse RGB string "r,g,b"
    int r = 0, g = 0, b = 0;
    int firstComma = rgb_str.indexOf(',');
    int secondComma = rgb_str.indexOf(',', firstComma + 1);
    
    if (firstComma != -1 && secondComma != -1) {
        r = rgb_str.substring(0, firstComma).toInt();
        g = rgb_str.substring(firstComma + 1, secondComma).toInt();
        b = rgb_str.substring(secondComma + 1).toInt();
    }

    analogWrite(redPin, r);
    analogWrite(greenPin, g);
    analogWrite(bluePin, b);

    distance = sonar.ping_cm();
    Bridge.call("set_distance", distance);

    float temperature = thermo.getTemperature();
    Bridge.call("set_temperature", temperature);

    float humidity = thermo.getHumidity();
    Bridge.call("set_humidity", humidity);

    if (left)
    {
        Monitor.print("Action: LEFT, speed=");
        Monitor.println(speed);
        right_servo.write(90 - speed);
        left_servo.write(90 - speed);
        delay(1000);
    }
    else if (right)
    {
        Monitor.print("Action: RIGHT, speed=");
        Monitor.println(speed);
        right_servo.write(90 + speed);
        left_servo.write(90 + speed);
        delay(1000);
    }
    else if (forward)
    {
        Monitor.print("Action: FORWARD, speed=");
        Monitor.println(speed);
        right_servo.write(90 - speed);
        left_servo.write(90 + speed);
        delay(1000);
    }
    else if (back)
    {
        Monitor.print("Action: BACK, speed=");
        Monitor.println(speed);
        right_servo.write(90 + speed);
        left_servo.write(90 - speed);
        delay(1000);
    }
    else if (agi)
    {
        right_servo.write(90);
        left_servo.write(90);
        Monitor.print("Action: AGI loop, distance=");
        Monitor.println(distance);
        if (distance == 0)
            distance = 1000; // no echo, set to max
        String mvcmd;
        Bridge.call("agi_loop", distance).result(mvcmd);
        Monitor.print("AGI cmd: ");
        Monitor.println(mvcmd);
        if (mvcmd.length() > 0)
        {
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
                Monitor.print("AGI MOVE verb parsed: ");
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
                    Monitor.println("AGI executing MOVE forward\n");
                    right_servo.write(90 - mvspd);
                    left_servo.write(90 + mvspd);
                    delay(ms);
                }
                else if (dir == "back")
                {
                    Monitor.println("AGI executing MOVE back\n");
                    right_servo.write(90 + mvspd);
                    left_servo.write(90 - mvspd);
                    delay(ms);
                }
                // stop
                right_servo.write(90);
                left_servo.write(90);
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
                float ms_per_deg_base = 30.0; // empirical base at speed 45
                float scale = (mvspd > 0) ? ((float)mvspd / 45.0) : 1.0;
                unsigned long ms = (unsigned long)(ang * ms_per_deg_base / scale);

                if (dir == "left")
                {
                    Monitor.println("AGI executing TURN left\n");
                    right_servo.write(90 - mvspd);
                    left_servo.write(90 - mvspd);
                    delay(ms);
                }
                else if (dir == "right")
                {
                    Monitor.println("AGI executing TURN right\n");
                    right_servo.write(90 + mvspd);
                    left_servo.write(90 + mvspd);
                    delay(ms);
                }
                right_servo.write(90);
                left_servo.write(90);
            }
            else if (verb == "STOP")
            {
                Monitor.println("AGI STOP\n");
                right_servo.write(90);
                left_servo.write(90);
            }
        }
    }
    else
    {
        right_servo.write(90);
        left_servo.write(90);
    }
}
