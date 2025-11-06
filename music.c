// SPDX-FileCopyrightText: Copyright (C) 2025 ARDUINO SA <http://www.arduino.cc>
//
// SPDX-License-Identifier: MPL-2.0

#include <Arduino_RouterBridge.h>
#include <Modulino.h>

ModulinoBuzzer buzzer;

// Define musical notes (frequencies in Hz)
const int NOTE_C4 = 262;
const int NOTE_D4 = 294;
const int NOTE_E4 = 330;
const int NOTE_F4 = 349;
const int NOTE_G4 = 392;

const int duration = 500;  // Duration of each note in milliseconds

// Smile frames
const uint32_t smile1[] = {
    0x904101f0,
    0x5f420212,
    0x41390a28,
    0x10,
};

const uint32_t smile2[] = {
    0x904101f0,
    0x51420212,
    0x808209c8,
    0xf,
};

const uint32_t smile3[] = {
    0x904101f0,
    0x5f420212,
    0x80820808,
    0xf,
};

const uint32_t smile4[] = {
    0x904101f0,
    0x4e420212,
    0xc1010a28,
    0x1f,
};

const uint32_t smile5[] = {
    0x904101f0,
    0x4042da12,
    0x808209c8,
    0xf,
};

// Animation control
unsigned long lastSmileChange = 0;
const unsigned long SMILE_CHANGE_INTERVAL = 1000; // Change smile every second

extern "C" void matrixWrite(const uint32_t* buf);
extern "C" void matrixBegin();


// Create a ModulinoMovement object
ModulinoMovement movement;

float x_accel, y_accel, z_accel; // Accelerometer values in g

unsigned long previousMillis = 0; // Stores last time values were updated
const long interval = 16;         // Interval at which to read (16ms) - sampling rate of 62.5Hz and should be adjusted based on model definition
int has_movement = 0;             // Flag to indicate if movement data is available

void setup() {
    Bridge.begin();
    matrixBegin();
    
    // Initialize Modulino I2C communication
    Modulino.begin(Wire1);
    buzzer.begin();
}

void loop() {
    unsigned long currentMillis = millis();
    
    // Change smile randomly every second
    if (currentMillis - lastSmileChange >= SMILE_CHANGE_INTERVAL) {
        // Pick a random smile (0-4)
        int randomSmile = random(5);
        switch(randomSmile) {
            case 0: matrixWrite(smile1); break;
            case 1: matrixWrite(smile2); break;
            case 2: matrixWrite(smile3); break;
            case 3: matrixWrite(smile4); break;
            case 4: matrixWrite(smile5); break;
        }
        lastSmileChange = currentMillis;
    }
    
    // Play "Jingle Bells" melody
    buzzer.tone(NOTE_E4, duration);  // Jin-
    delay(duration);
    buzzer.tone(NOTE_E4, duration);  // gle
    delay(duration);
    buzzer.tone(NOTE_E4, duration);  // bells
    delay(duration * 2);             // Pause

    buzzer.tone(NOTE_E4, duration);  // Jin-
    delay(duration);
    buzzer.tone(NOTE_E4, duration);  // gle
    delay(duration);
    buzzer.tone(NOTE_E4, duration);  // bells
    delay(duration * 2);             // Pause

    buzzer.tone(NOTE_E4, duration);  // Jin-
    delay(duration);
    buzzer.tone(NOTE_G4, duration);  // gle
    delay(duration);
    buzzer.tone(NOTE_C4, duration);  // all
    delay(duration);
    buzzer.tone(NOTE_D4, duration);  // the
    delay(duration);
    buzzer.tone(NOTE_E4, duration);  // way
    delay(duration * 2);             // Longer pause

    delay(1000);  // Shorter pause before repeating


}
