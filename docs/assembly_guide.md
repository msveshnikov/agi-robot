# AGI Robot Assembly Guide

Welcome to the assembly guide for the **AGI Robot**—a fully autonomous, LLM-powered mobile explorer. This guide will walk you through 3D printing the chassis, assembling the mechanical components, and wiring the electronics.

---

## 🛠️ Bill of Materials (BOM)

| Category | Item | Quantity | Links (AE / AMZ) |
| :--- | :--- | :---: | :--- |
| **Microcontroller** | Arduino Uno Q)| 1 | [AE](https://www.aliexpress.com/w/wholesale-Arduino-Uno-Q.html) / [AMZ](amazon.com/Arduino-2-GB-ABX00162-microprocessor-Microcontroller/dp/B0FVLQLMSV/ref=sr_1_2?dib=eyJ2IjoiMSJ9.wCPx8spVnJsCoaDKXV6Y_KySTyn4Hi8jrl9-q3Ek4tihCjwKffUmlxrS9cl9yeSRr3noAOUEEW-UZP0QDf4HseKgc8yYq8Rspk1qmX1_sk0STF7St8MEF94nME0-WW3yH0AYtCAwdQxHh-hTH2x1TflnPbV-OaRLxOiGz2kV1HL1eFfCJRUVfZR8SWWpeANraHxrNijAR_LYrJWqghxRu5KT2wOzE3hmZcXlcUgsbF8.ysFFoNQY4csQhMvSE1P5qcII3MzDYdGwWBqFShuw9vo&dib_tag=se&keywords=uno+q&qid=1771419151&sr=8-2) |
| **Actuators** | SG90 360° Continuous Servo | 2 | [AE](https://www.aliexpress.com/w/wholesale-SG90+360+servo.html) / [AMZ](https://www.amazon.com/s?k=SG90+360+degree+servo) |
| **Actuators** | SG90 180° Standard Servo | 2 | [AE](https://www.aliexpress.com/w/wholesale-SG90+180+servo.html) / [AMZ](https://www.amazon.com/s?k=SG90+servo) |
| **Vision** | USB Webcam with Microphone | 1 | [AE](https://www.aliexpress.com/w/wholesale-usb+webcam+microphone.html) / [AMZ](https://www.amazon.com/s?k=usb+webcam+with+microphone) |
| **Audio** | Mini Bluetooth/USB Speaker | 1 | [AE](https://www.aliexpress.com/w/wholesale-mini+bluetooth+speaker.html) / [AMZ](https://www.amazon.com/s?k=mini+bluetooth+speaker) |
| **Sensors** | HC-SR04 Ultrasonic Sensor | 1 | [AE](https://www.aliexpress.com/w/wholesale-HC-SR04.html) / [AMZ](https://www.amazon.com/s?k=HC-SR04) |
| **Sensors** | Modulino Thermo (I2C) | 1 | [Arduino](https://store.arduino.cc/products/arduino-modulino-thermo) / [AMZ](https://www.amazon.com/s?k=Arduino+Modulino+Thermo) |
| **Lighting** | RGB LED (Common Cathode) | 1 | [AE](https://www.aliexpress.com/w/wholesale-RGB+LED+common+cathode.html) / [AMZ](https://www.amazon.com/s?k=RGB+LED+common+cathode) |
| **Power** | 10000 mAh PowerBank | 1 | [AE](https://www.aliexpress.com/w/wholesale-Xiaomi+Powerbank+10000.html) / [AMZ](https://www.amazon.com/s?k=10000mAh+Power+Bank) |
| **Connectivity** | USB-C to USB-A Hub | 1 | [AE](https://www.aliexpress.com/w/wholesale-usb-c+hub+4+usb-a.html) / [AMZ](https://www.amazon.com/s?k=usb-c+hub+to+usb-a) |
| **Prototyping** | Breadboard & Jumper Wires | - | [AE](https://www.aliexpress.com/w/wholesale-breadboard+wires+kit.html) / [AMZ](https://www.amazon.com/s?k=breadboard+and+jumper+wires+kit) |
| **Structure** | 3D Printed Parts (PLA/PETG) | ~200g | $3 |

---

## 🖨️ 3D Printing

All models are located in the [/3d](../3d) folder.

### Core Components
- **[Chassis.stl](../3d/Chassis.stl)**: The main body that holds the breadboard and Arduino.
- **[Cabin.stl](../3d/Cabin.stl)**: The top cover (roof) where the camera and arm are mounted.
- **[Arduino_Base.stl](../3d/Arduino_Base.stl)**: Mount for the Arduino Uno.

### Drive System
- **[Parametric_wheel.stl](../3d/Parametric_wheel.stl)**: Two required for the front drive.
- **[Tire.stl](../3d/Tire.stl)**: Flexible tires for the wheels.
- **[Rear_wheel.stl](../3d/Rear_wheel.stl)**: Small trailing wheel for stability.

### Manipulator & Mounts
- **[Arm1.stl](../3d/Arm1.stl)** & **[Arm2.stl](../3d/Arm2.stl)**: The two segments of the robot arm.
- **[Servo_Mount.stl](../3d/Servo_Mount.stl)**: Support for the arm servos.
- **[Webcam_mount.stl](../3d/Webcam_mount.stl)**: Tilting mount for the camera.

---

## 🔧 Mechanical Assembly

### 1. The Chassis
1. **Mount the Servos**: Insert the two 360° SG90 servos into the slots on the side of the [Chassis.stl](../3d/Chassis.stl).
2. **Arduino & Breadboard**: Place the [Arduino_Base.stl](../3d/Arduino_Base.stl) inside the chassis. Slot the breadboard next to it.
3. **Wheels**: Press-fit the [Parametric_wheel.stl](../3d/Parametric_wheel.stl) onto the servo shafts. Add the [Tire.stl](../3d/Tire.stl) for traction.

### 2. The Head & Cabin
1. **Ultrasonic Sensor**: Snap the HC-SR04 into the two circular holes at the front of the [Cabin.stl](../3d/Cabin.stl).
2. **Webcam**: Use the [Webcam_mount.stl](../3d/Webcam_mount.stl) to attach the camera to the roof.
3. **Manipulator Arm**: Assemble [Arm1.stl](../3d/Arm1.stl) and [Arm2.stl](../3d/Arm2.stl) using the 180° servos and mount them on top of the cabin.

---

## ⚡ Electronics & Wiring

The heart of the robot is the Arduino Uno Q. Connect the components according to the table below:

| Component | Arduino Pin | Wire Color (Typical) |
| :--- | :---: | :--- |
| **Left Wheel Servo** | **D11** | Signal (Orange/White) |
| **Right Wheel Servo** | **D10** | Signal (Orange/White) |
| **Arm Servo 1 (Base)** | **D3** | Signal (Orange/White) |
| **Arm Servo 2 (Joint)** | **D5** | Signal (Orange/White) |
| **Ultrasonic Trig** | **D8** | Trigger |
| **Ultrasonic Echo** | **D9** | Echo |
| **RGB LED (Red)** | **D4** | Red Leg |
| **RGB LED (Green)** | **D6** | Green Leg |
| **RGB LED (Blue)** | **D2** | Blue Leg |
| **Modulino Thermo** | **I2C** | Qwiic Connector |

> [!IMPORTANT]
> **Power Connection**: All servos and the Arduino should share a common ground (GND). Ensure your PowerBank can provide at least 2A of current to prevent brownouts during movement.

---

## 🚀 Software Setup

### 1. Arduino Firmware
- Connect the Arduino Uno Q to your PC.
- ssh or adb to board
- cd ~/ArduinoApps
- git pull https://github.com/mvpgen/agi-robot.git
- Start AppLab and navigate to the agi-robot application
- Click "Run" and "Set up as default"

### 2. Python Environment (MPU)
- Ensure you have Python 3.12+ installed on the robot's Linux environment.
- Install dependencies:
  ```bash
  pip install arduino-app-utils google-genai google-api-python-client python-socketio[client]
  ```
- Set your `GEMINI_KEY` and path to `google.json`.

### 3. Running the Robot
- Start the media service: `python python/media_service.py`
- Start the main control loop: `python python/main.py`
- Open the dashboard at [robot.mvpgen.com](https://robot.mvpgen.com) to take control!

---

![Robot Interior Wiring](image-3.jpg)
*Interior view showing breadboard, Arduino, and USB hub placement.*

![Robot Final Build](image-1.jpg)
*The fully assembled robot with cabin and sensors.*
