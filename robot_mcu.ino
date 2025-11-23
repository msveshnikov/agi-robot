#include <Arduino_RouterBridge.h>
#include <Servo.h>
#include <Arduino_LED_Matrix.h>

// Configuration
const int MAX_SERVOS = 2; // Left and Right wheels
const int LEFT_SERVO_PIN = 5;
const int RIGHT_SERVO_PIN = 6;
const int SENSOR_PIN = A0; // Placeholder for sensor
const int EYE_LEFT_PIN = 2;
const int EYE_RIGHT_PIN = 3;

Servo leftServo;
Servo rightServo;
Arduino_LED_Matrix matrix;

// Emotion Frames (12x8)
// Each frame is 3 uint32_t values
const uint32_t EMOTION_NEUTRAL[][4] = {
    { 0x00000000, 0x00000000, 0x00000000, 66000000 }, // No frame? Wait, let's use the raw hex format for simplicity or a byte array if using matrix.loadFrame
    // Actually, let's use the 3x uint32_t format which is standard for this library's loadFrame/renderBitmap
    // 12 columns, 8 rows.
    // We will use a simpler approach: define them as 2D byte arrays and convert or just use the hex values.
    // Let's use the hex values for 12x8.
    // R4 Matrix is 96 bits.
    // 0: Neutral
    { 0x30003000, 0x30003000, 0x00000000 }, // Eyes only?
    // Let's try to draw them mentally.
    // 001100000000 -> 0x300
    // ...
};

// Better approach: Use the "bitmap" format which is 3 unsigned longs.
// Neutral: Eyes open, straight mouth.
const uint32_t emotions[][3] = {
    { 0x0C003000, 0x0C003000, 0x00000000 }, // 0: Neutral (Placeholder)
    { 0x0C003000, 0x0C003000, 0x30000C00 }, // 1: Happy (Smile)
    { 0x0C003000, 0x0C003000, 0x0C003000 }, // 2: Sad (Frown - inverted smile needed)
    { 0x0C003000, 0x0C003000, 0x00000000 }, // 3: Angry
    { 0x0C003000, 0x0C003000, 0x00000000 }  // 4: Surprised
};

// Let's refine the bitmaps.
// 12x8 matrix.
// Row 0-7.
// 3x 32-bit integers.
// This is hard to hand-code. I'll use a simple placeholder for now and we can refine if needed.
// Or I can use the byte frame buffer method which is easier to visualize.

uint8_t frame[8][12] = {
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  {0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0},
  {0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  {0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0},
  {0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
};

void drawEmotion(int emotionId) {
    // Reset frame
    for(int r=0; r<8; r++) for(int c=0; c<12; c++) frame[r][c] = 0;

    // Eyes (always present for now)
    frame[1][2] = 1; frame[1][3] = 1; frame[2][2] = 1; frame[2][3] = 1;
    frame[1][8] = 1; frame[1][9] = 1; frame[2][8] = 1; frame[2][9] = 1;

    switch(emotionId) {
        case 0: // Neutral
            for(int i=3; i<=8; i++) frame[6][i] = 1;
            break;
        case 1: // Happy
            frame[5][2] = 1; frame[5][9] = 1;
            frame[6][3] = 1; frame[6][8] = 1;
            for(int i=4; i<=7; i++) frame[7][i] = 1;
            break;
        case 2: // Sad
            for(int i=3; i<=8; i++) frame[5][i] = 1;
            frame[6][2] = 1; frame[6][9] = 1;
            break;
        case 3: // Angry
            // Angled eyebrows
            frame[0][2] = 1; frame[0][9] = 1;
            frame[1][3] = 1; frame[1][8] = 1;
            // Mouth
            for(int i=3; i<=8; i++) frame[6][i] = 1;
            break;
        case 4: // Surprised
            // O mouth
            for(int i=4; i<=7; i++) { frame[5][i] = 1; frame[7][i] = 1; }
            frame[6][3] = 1; frame[6][8] = 1;
            break;
    }
    
    matrix.renderBitmap(frame, 8, 12);
}

// Bridge function to set servo angle (Legacy support, though we mainly use L/R commands now)
void set_servo(int index, int angle) {
  angle = constrain(angle, 0, 180);
  if (index == 0) leftServo.write(angle);
  else if (index == 1) rightServo.write(angle);
  Bridge.returnResult(true);
}

void setup() {
  // Initialize Bridge
  Bridge.begin();
  
  // Initialize Matrix
  matrix.begin();
  drawEmotion(0); // Start neutral

  // Initialize Eye LEDs
  pinMode(EYE_LEFT_PIN, OUTPUT);
  pinMode(EYE_RIGHT_PIN, OUTPUT);
  digitalWrite(EYE_LEFT_PIN, LOW); // Start off
  digitalWrite(EYE_RIGHT_PIN, LOW);
  
  // Attach servos
  leftServo.attach(LEFT_SERVO_PIN);
  rightServo.attach(RIGHT_SERVO_PIN);
  
  // Stop motors initially (90 is usually stop for continuous rotation servos)
  leftServo.write(90);
  rightServo.write(90);
  
  // Register Bridge functions
  Bridge.provide("set_servo", set_servo);
}

void parseAndExecute(String cmdString) {
  // Format: "L<angle>;R<angle>;E<emotion_id>;Y<eyes_state>" 
  // e.g. "L100;R80;E1;Y11"
  
  int startIdx = 0;
  int separatorIdx = cmdString.indexOf(';');
  
  while (startIdx < cmdString.length()) {
      String part;
      if (separatorIdx == -1) {
          part = cmdString.substring(startIdx);
          startIdx = cmdString.length();
      } else {
          part = cmdString.substring(startIdx, separatorIdx);
          startIdx = separatorIdx + 1;
          separatorIdx = cmdString.indexOf(';', startIdx);
      }
      
      if (part.length() == 0) continue;
      
      char type = part.charAt(0);
      String valStr = part.substring(1);
      
      if (type == 'L') {
          int angle = valStr.toInt();
          leftServo.write(constrain(angle, 0, 180));
      } else if (type == 'R') {
          int angle = valStr.toInt();
          rightServo.write(constrain(angle, 0, 180));
      } else if (type == 'E') {
          int emotion = valStr.toInt();
          drawEmotion(emotion);
      } else if (type == 'Y') {
          // Expecting "11", "10", "01", "00"
          if (valStr.length() >= 2) {
              digitalWrite(EYE_LEFT_PIN, valStr.charAt(0) == '1' ? HIGH : LOW);
              digitalWrite(EYE_RIGHT_PIN, valStr.charAt(1) == '1' ? HIGH : LOW);
          }
      }
  }
}

void loop() {
  // 1. Ask Python for commands
  String command;
  if (Bridge.call("tick").result(command)) {
    if (command != "NOOP" && command.length() > 0) {
      parseAndExecute(command);
    }
  }
  
  // 2. Read Sensors and send to Python
  int sensorValue = analogRead(SENSOR_PIN);
  // We can send this every loop or periodically. Let's do it every loop for now.
  Bridge.call("update_sensors", sensorValue);
  
  // Small delay
  delay(50);
}
