#include <Servo.h>

// Configuration
const int MAX_SERVOS = 4;
const int SERVO_PINS[MAX_SERVOS] = {3, 5, 6, 9}; // PWM pins on standard Arduino
const int BAUD_RATE = 115200;

Servo servos[MAX_SERVOS];
String inputString = "";
boolean stringComplete = false;

void setup() {
  Serial.begin(BAUD_RATE);
  
  // Attach servos
  for (int i = 0; i < MAX_SERVOS; i++) {
    servos[i].attach(SERVO_PINS[i]);
    servos[i].write(90); // Default to center
  }
  
  inputString.reserve(200);
  Serial.println("READY: Servos attached");
}

void loop() {
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
}

/*
  SerialEvent occurs whenever a new data comes in the hardware serial RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

void processCommand(String command) {
  command.trim();
  
  // Protocol: S<index>:<angle>
  // Example: S0:90 (Set servo 0 to 90 degrees)
  
  if (command.startsWith("S")) {
    int separatorIndex = command.indexOf(':');
    if (separatorIndex > 1) {
      int servoIndex = command.substring(1, separatorIndex).toInt();
      int angle = command.substring(separatorIndex + 1).toInt();
      
      if (servoIndex >= 0 && servoIndex < MAX_SERVOS) {
        angle = constrain(angle, 0, 180);
        servos[servoIndex].write(angle);
        Serial.print("OK: Servo ");
        Serial.print(servoIndex);
        Serial.print(" -> ");
        Serial.println(angle);
      } else {
        Serial.println("ERR: Invalid servo index");
      }
    } else {
      Serial.println("ERR: Invalid format");
    }
  } else {
    Serial.println("ERR: Unknown command");
  }
}
