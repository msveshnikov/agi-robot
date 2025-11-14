#include <Arduino_RouterBridge.h>
#include <Modulino.h>

extern "C" void matrixWrite(const uint32_t *buf);
extern "C" void matrixBegin();

// Create Modulino Thermo object instance
ModulinoThermo thermo;

// ========== LARGE DIGIT PATTERNS (for temperature) ==========
const uint32_t digit0[] = {
    0x0E, // 01110
    0x11, // 10001
    0x11, // 10001
    0x11, // 10001
    0x11, // 10001
    0x0E, // 01110
    0x00,
    0x00,
};

const uint32_t digit1[] = {
    0x04, // 00100
    0x0C, // 01100
    0x04, // 00100
    0x04, // 00100
    0x04, // 00100
    0x0E, // 01110
    0x00,
    0x00,
};

const uint32_t digit2[] = {
    0x0E, // 01110
    0x11, // 10001
    0x01, // 00001
    0x0E, // 01110
    0x10, // 10000
    0x1F, // 11111
    0x00,
    0x00,
};

const uint32_t digit3[] = {
    0x0E, // 01110
    0x11, // 10001
    0x01, // 00001
    0x0E, // 01110
    0x01, // 00001
    0x1E, // 11110
    0x00,
    0x00,
};

const uint32_t digit4[] = {
    0x11, // 10001
    0x11, // 10001
    0x11, // 10001
    0x1F, // 11111
    0x01, // 00001
    0x01, // 00001
    0x00,
    0x00,
};

const uint32_t digit5[] = {
    0x1F, // 11111
    0x10, // 10000
    0x10, // 10000
    0x1E, // 11110
    0x01, // 00001
    0x1E, // 11110
    0x00,
    0x00,
};

const uint32_t digit6[] = {
    0x0E, // 01110
    0x10, // 10000
    0x10, // 10000
    0x1E, // 11110
    0x11, // 10001
    0x0E, // 01110
    0x00,
    0x00,
};

const uint32_t digit7[] = {
    0x1F, // 11111
    0x01, // 00001
    0x02, // 00010
    0x04, // 00100
    0x08, // 01000
    0x08, // 01000
    0x00,
    0x00,
};

const uint32_t digit8[] = {
    0x0E, // 01110
    0x11, // 10001
    0x11, // 10001
    0x0E, // 01110
    0x11, // 10001
    0x0E, // 01110
    0x00,
    0x00,
};

const uint32_t digit9[] = {
    0x0E, // 01110
    0x11, // 10001
    0x11, // 10001
    0x0F, // 01111
    0x01, // 00001
    0x0E, // 01110
    0x00,
    0x00,
};

const uint32_t *digits[10] = {
    digit0, digit1, digit2, digit3, digit4,
    digit5, digit6, digit7, digit8, digit9};

// ========== SMALL DIGIT PATTERNS (for time - 3x5) ==========
const uint32_t smallDigit0[] = {
    0x07, // 111
    0x05, // 101
    0x05, // 101
    0x05, // 101
    0x07, // 111
};

const uint32_t smallDigit1[] = {
    0x02, // 010
    0x06, // 110
    0x02, // 010
    0x02, // 010
    0x07, // 111
};

const uint32_t smallDigit2[] = {
    0x07, // 111
    0x01, // 001
    0x07, // 111
    0x04, // 100
    0x07, // 111
};

const uint32_t smallDigit3[] = {
    0x07, // 111
    0x01, // 001
    0x07, // 111
    0x01, // 001
    0x07, // 111
};

const uint32_t smallDigit4[] = {
    0x05, // 101
    0x05, // 101
    0x07, // 111
    0x01, // 001
    0x01, // 001
};

const uint32_t smallDigit5[] = {
    0x07, // 111
    0x04, // 100
    0x07, // 111
    0x01, // 001
    0x07, // 111
};

const uint32_t smallDigit6[] = {
    0x07, // 111
    0x04, // 100
    0x07, // 111
    0x05, // 101
    0x07, // 111
};

const uint32_t smallDigit7[] = {
    0x07, // 111
    0x01, // 001
    0x02, // 010
    0x02, // 010
    0x02, // 010
};

const uint32_t smallDigit8[] = {
    0x07, // 111
    0x05, // 101
    0x07, // 111
    0x05, // 101
    0x07, // 111
};

const uint32_t smallDigit9[] = {
    0x07, // 111
    0x05, // 101
    0x07, // 111
    0x01, // 001
    0x07, // 111
};

const uint32_t *smallDigits[10] = {
    smallDigit0, smallDigit1, smallDigit2, smallDigit3, smallDigit4,
    smallDigit5, smallDigit6, smallDigit7, smallDigit8, smallDigit9};

// ========== WEATHER ANIMATIONS ==========
const uint32_t Sunny[] = {
    0xa0148120,
    0x9c1c801,
    0x409402c0,
    0x2};
const uint32_t Sunny2[] = {
    0x804a0048,
    0x39004e05,
    0x2900d0,
    0x9};
const uint32_t *SunnyFrames[] = {Sunny, Sunny2};

const uint32_t Cloudy[] = {
    0x701c0000,
    0x20211104,
    0x7f0404,
    0x0};
const uint32_t Cloudy2[] = {
    0xe0380000,
    0x40422208,
    0xfe0808,
    0x0};
const uint32_t Cloudy3[] = {
    0xc0700000,
    0x80844411,
    0x1fc1010,
    0x0};
const uint32_t Cloudy4[] = {
    0xe0380000,
    0x40422208,
    0xfe0808,
    0x0};
const uint32_t *CloudyFrames[] = {Cloudy, Cloudy2, Cloudy3, Cloudy4};

const uint32_t Rainy[] = {
    0x104301e0,
    0x3f820210,
    0x8a0510,
    0x5};
const uint32_t Rainy2[] = {
    0x104301e0,
    0x3f820210,
    0x40a20140,
    0x11};
const uint32_t Rainy3[] = {
    0x104301e0,
    0x3f820210,
    0x40280450,
    0x14};
const uint32_t *RainyFrames[] = {Rainy, Rainy2, Rainy3};

const uint32_t Snowy[] = {
    0x104301e0,
    0x3f820210,
    0x220040,
    0x11};
const uint32_t Snowy2[] = {
    0x104301e0,
    0x3f820210,
    0x40080400,
    0x4};
const uint32_t Snowy3[] = {
    0x104301e0,
    0x3f820210,
    0x800110,
    0x1};
const uint32_t *SnowyFrames[] = {Snowy, Snowy2, Snowy3};

const uint32_t Foggy[] = {
    0xdf8000,
    0x3f600,
    0xef8,
    0x0};
const uint32_t Foggy2[] = {
    0xf78000,
    0x3ee00,
    0xdf8,
    0x0};
const uint32_t *FoggyFrames[] = {Foggy, Foggy2};

// ========== DISPLAY FUNCTIONS ==========
uint32_t displayBuffer[4];

void displayNumber(int num)
{
    if (num < 0)
        num = 0;
    if (num > 99)
        num = 99;

    int tens = num / 10;
    int ones = num % 10;

    displayBuffer[0] = 0;
    displayBuffer[1] = 0;
    displayBuffer[2] = 0;
    displayBuffer[3] = 0;

    auto reverseBits5 = [](uint32_t val) -> uint32_t
    {
        return ((val & 0x01) << 4) | ((val & 0x02) << 2) | (val & 0x04) |
               ((val & 0x08) >> 2) | ((val & 0x10) >> 4);
    };

    // Celsius degree symbol (small circle at top right)
    // Position: bit 11 (rightmost area)
    uint32_t celsiusRow0 = 0x03 << 11; // 11
    uint32_t celsiusRow1 = 0x03 << 11; // 11

    uint32_t row0 = reverseBits5(digits[tens][0] & 0x1F) | (reverseBits5(digits[ones][0] & 0x1F) << 6) | celsiusRow0;
    uint32_t row1 = reverseBits5(digits[tens][1] & 0x1F) | (reverseBits5(digits[ones][1] & 0x1F) << 6) | celsiusRow1;
    uint32_t row2 = reverseBits5(digits[tens][2] & 0x1F) | (reverseBits5(digits[ones][2] & 0x1F) << 6);
    uint32_t row3 = reverseBits5(digits[tens][3] & 0x1F) | (reverseBits5(digits[ones][3] & 0x1F) << 6);
    uint32_t row4 = reverseBits5(digits[tens][4] & 0x1F) | (reverseBits5(digits[ones][4] & 0x1F) << 6);
    uint32_t row5 = reverseBits5(digits[tens][5] & 0x1F) | (reverseBits5(digits[ones][5] & 0x1F) << 6);
    uint32_t row6 = 0;
    uint32_t row7 = 0;

    displayBuffer[0] = row0 | (row1 << 13) | (row2 << 26);
    displayBuffer[1] = (row2 >> 6) | (row3 << 7) | (row4 << 20);
    displayBuffer[2] = (row4 >> 12) | (row5 << 1) | (row6 << 14) | (row7 << 27);
    displayBuffer[3] = (row7 >> 5);

    matrixWrite(displayBuffer);
}

void displayTime(int hours, int minutes, bool showColon)
{
    displayBuffer[0] = 0;
    displayBuffer[1] = 0;
    displayBuffer[2] = 0;
    displayBuffer[3] = 0;

    int h1 = hours / 10;
    int h2 = hours % 10;
    int m1 = minutes / 10;
    int m2 = minutes % 10;

    auto reverseBits3 = [](uint32_t val) -> uint32_t
    {
        return ((val & 0x01) << 2) | (val & 0x02) | ((val & 0x04) >> 2);
    };

    // Build time display: HH:MM with small 3x5 digits
    // Layout: 3 + 3 + 1 + 3 + 3 = 13 bits wide (perfect fit!)

    for (int row = 0; row < 5; row++)
    {
        uint32_t rowData = 0;

        // Hours tens digit (bits 0-2)
        rowData |= reverseBits3(smallDigits[h1][row] & 0x07);

        // Hours ones digit (bits 3-5)
        rowData |= reverseBits3(smallDigits[h2][row] & 0x07) << 3;

        // Colon (bit 6) - one dot at rows 1 and 3
        if (showColon && (row == 1 || row == 3))
        {
            rowData |= 0x01 << 6;
        }

        // Minutes tens digit (bits 7-9)
        rowData |= reverseBits3(smallDigits[m1][row] & 0x07) << 7;

        // Minutes ones digit (bits 10-12)
        rowData |= reverseBits3(smallDigits[m2][row] & 0x07) << 10;

        // Pack row into display buffer (centered vertically, starting at row 1)
        if (row == 0)
        {
            displayBuffer[0] |= (rowData << 13);
        }
        else if (row == 1)
        {
            displayBuffer[0] |= (rowData << 26);
            displayBuffer[1] |= (rowData >> 6);
        }
        else if (row == 2)
        {
            displayBuffer[1] |= (rowData << 7);
        }
        else if (row == 3)
        {
            displayBuffer[1] |= (rowData << 20);
            displayBuffer[2] |= (rowData >> 12);
        }
        else if (row == 4)
        {
            displayBuffer[2] |= (rowData << 1);
        }
    }

    matrixWrite(displayBuffer);
}

void playAnimation(const uint32_t *frames[], int frameCount, int totalDuration, int frameDelay)
{
    unsigned long startTime = millis();

    while (millis() - startTime < totalDuration)
    {
        for (int i = 0; i < frameCount; i++)
        {
            matrixWrite(frames[i]);
            delay(frameDelay);

            if (millis() - startTime >= totalDuration)
            {
                return;
            }
        }
    }
}

// ========== SETUP AND LOOP ==========
void setup()
{
    matrixBegin();
    Bridge.begin();
    Monitor.begin();

    // Initialize Modulino I2C communication
    Modulino.begin(Wire1);

    // Detect and connect to temperature/humidity sensor module
    thermo.begin();
}

void loop()
{
    // 1. Display time for 5 seconds with blinking colon
    String timeStr;
    bool timeOk = Bridge.call("get_time").result(timeStr);

    if (timeOk)
    {
        // Parse time string "HH:MM"
        int colonPos = timeStr.indexOf(':');
        if (colonPos > 0)
        {
            int hours = timeStr.substring(0, colonPos).toInt();
            int minutes = timeStr.substring(colonPos + 1).toInt();

            // Display for 5 seconds with blinking colon
            unsigned long startTime = millis();
            while (millis() - startTime < 5000)
            {
                bool showColon = ((millis() / 1000) % 2) == 0; // Blink every second
                displayTime(hours, minutes, showColon);
                delay(100); // Update every 100ms for smooth blinking
            }
        }
    }
    else
    {
        delay(5000); // If time fetch fails, wait 5 seconds
    }

    // 2. Display real temperature from Modulino Thermo for 5 seconds
    float celsius = thermo.getTemperature();
    int realTemp = (int)celsius;
    Monitor.print("Inside Temperature: ");
    Monitor.println(realTemp);
    if (realTemp < 0)
        realTemp = 0;
    displayNumber(realTemp);
    delay(5000);

    // 3. Display humidity from Modulino Thermo for 5 seconds
    float humidityFloat = thermo.getHumidity();
    int humidity = (int)humidityFloat;
    Monitor.print("Humidity: ");
    Monitor.println(humidity);
    if (humidity < 0)
        humidity = 0;
    if (humidity > 99)
        humidity = 99;
    displayNumber(humidity);
    delay(5000);

    // 4. Display forecast temperature for 5 seconds
    int temperature;
    bool tempOk = Bridge.call("get_temperature").result(temperature);
    Monitor.print("Outside Temperature: ");
    Monitor.println(temperature);
    if (tempOk)
    {
        if (temperature < 0)
            temperature = 0;
        displayNumber(temperature);
        delay(5000);
    }
    else
    {
        delay(5000);
    }

    // 5. Display weather animation for 5 seconds
    String weather_forecast;
    bool condOk = Bridge.call("get_conditions").result(weather_forecast);

    if (condOk)
    {
        if (weather_forecast == "Clear")
        {
            playAnimation(SunnyFrames, 2, 5000, 500);
        }
        else if (weather_forecast == "Clouds")
        {
            playAnimation(CloudyFrames, 4, 5000, 300);
        }
        else if (weather_forecast == "Rain" || weather_forecast == "Drizzle")
        {
            playAnimation(RainyFrames, 3, 5000, 400);
        }
        else if (weather_forecast == "Snow")
        {
            playAnimation(SnowyFrames, 3, 5000, 600);
        }
        else if (weather_forecast == "Mist" || weather_forecast == "Fog" || weather_forecast == "Haze")
        {
            playAnimation(FoggyFrames, 2, 5000, 600);
        }
        else
        {
            playAnimation(CloudyFrames, 4, 5000, 300);
        }
    }
    else
    {
        delay(5000);
    }
}