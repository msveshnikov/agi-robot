#include <Arduino_RouterBridge.h>

// Function declarations for Arduino UNO Q LED Matrix
extern "C" void matrixWrite(const uint32_t* buf);
extern "C" void matrixBegin();

// Digit patterns for 8x13 LED matrix - explicit 6 columns (each column = 8 bits)
// Each digit occupies 6 columns (6x8). Columns are vertical bytes, index 0..5.
const uint8_t DIGITS[10][6] = {
    // 0
    { 0xF0, 0x01, 0x41, 0x90, 0x12, 0x02 },
    // 1
    { 0xC0, 0x01, 0x41, 0x90, 0x02, 0x02 },
    // 2
    { 0xF0, 0x01, 0x41, 0x90, 0x02, 0x00 },
    // 3
    { 0xF0, 0x01, 0x41, 0x90, 0x12, 0x00 },
    // 4
    { 0x88, 0x00, 0x41, 0x90, 0xF2, 0x01 },
    // 5
    { 0xF0, 0x01, 0x41, 0x90, 0x10, 0x02 },
    // 6
    { 0xF0, 0x01, 0x41, 0x90, 0x10, 0x02 },
    // 7
    { 0xF0, 0x01, 0x41, 0x90, 0x02, 0x00 },
    // 8
    { 0xF0, 0x01, 0x41, 0x90, 0x12, 0x02 },
    // 9
    { 0xF0, 0x01, 0x41, 0x90, 0x12, 0x02 }
};

// Buffer to store the final display pattern as 13 vertical columns (each column = 8 bits)
// Columns indexed 0..12 (13 columns). Each byte represents 8 vertical pixels.
uint8_t displayCols[13] = {0};

// Helper: get a single column byte from the explicit DIGITS table
static inline uint8_t getDigitColumnByte(int digit, int colIndex) {
    if (digit < 0 || digit >= 10) return 0;
    if (colIndex < 0 || colIndex >= 6) return 0;
    return DIGITS[digit][colIndex];
}

// Place a 6-column (6x8) digit into displayCols using logical OR.
// Left digit -> columns 0..5, Right digit -> columns 7..12 (column 6 is gap).
void displayDigit(int digit, bool isLeftDigit) {
    int destOffset = isLeftDigit ? 0 : 7; // left: cols 0-5, right: cols 7-12
    for (int c = 0; c < 6; ++c) {
        uint8_t colByte = getDigitColumnByte(digit, c);
        int dest = destOffset + c;
        if (dest >= 0 && dest < 13) {
            displayCols[dest] |= colByte; // OR - combine without overwriting
        }
    }
}

void displayNumber(int number) {
    // Clear columns
    for (int i = 0; i < 13; ++i) displayCols[i] = 0;

    if (number >= 10) {
        int tens = number / 10;
        int ones = number % 10;
        displayDigit(tens, true);   // first 6 columns (0-5)
        displayDigit(ones, false);  // last 6 columns (7-12)
    } else {
        // Single digit displayed on right side (columns 7-12)
        displayDigit(number, false);
    }

    // Pack the 13 bytes into 4 uint32_t words (little-endian byte order)
    uint32_t packed[4] = {0, 0, 0, 0};
    for (int i = 0; i < 13; ++i) {
        int wi = i / 4;
        int bi = i % 4;
        packed[wi] |= ((uint32_t)displayCols[i]) << (bi * 8);
    }

    // Write to display
    matrixWrite(packed);
}



void setup() {
    Serial.begin(9600);  // Initialize Serial communication
    matrixBegin();
    Bridge.begin();
    Serial.println("Temperature logging started");
}

void loop() {
    int temperature;
    bool ok = Bridge.call("get_temperature").result(temperature);
    
    if (ok) {
        if(temperature < 0) temperature = 0;
        displayNumber(temperature);
        
        // Log the temperature reading
        Serial.print("Temperature: ");
        Serial.print(temperature);
        Serial.println("°C");
    } else {
        Serial.println("Failed to read temperature");
    }
    delay(1000);
}
