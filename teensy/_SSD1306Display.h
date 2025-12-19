// EXAMPLE USAGE:
// #include "_SSD1306Display.h"
// SSD1306Display* display = new SSD1306Display();
// display->showArdString(String(millisSinceSync));

#include <Wire.h>        
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
//I2C communcation for the Adafruit SSD1306 display

class SSD1306Display{
  public:
    Adafruit_SSD1306 display;

    uint8_t SCREEN_WIDTH = 128;
    int SCREEN_HEIGHT = 64;
    byte address = 0x3C;

    SSD1306Display() : display(128, 64, &Wire, -1){
      display.begin(SSD1306_SWITCHCAPVCC, address);
      display.clearDisplay();
      display.display();
    }

    void showTime(unsigned long ms, unsigned long us){
      //running the display will drop the communication from ~5000 handshakes/s to ~1000
      display.clearDisplay();
      display.setTextSize(1);
      display.setTextColor(WHITE);
      display.setCursor(0, 10);
      display.println(ms);
      display.setCursor(0,20);
      display.println(us);
      display.display();
    }

    void showArdString(String str){
      //running the display will drop the communication from ~5000 handshakes/s to ~1000
      //Please only use Arduino strings during development/debugging, and not in the final version
      display.clearDisplay();
      display.setTextSize(1);
      display.setTextColor(WHITE);
      display.setCursor(0, 10);
      display.println(str);
      display.display();
    }
};