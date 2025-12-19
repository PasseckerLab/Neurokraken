#if __has_include("modes.h") //modes.h file exists
#  include "modes.h"
#endif
// to run in direct mode instead of archivist mode (only send current values, don't maintain/send 
// log of changes) add a file modes.h and include the line:
// #define DIRECT_MODE

#include "_Utils.h"

// #include "_SSD1306Display.h"
// SSD1306Display* display = new SSD1306Display();

#include "_Networker.h"

namespace krakenVars{
  // global variables
  // active/inactive control
  bool active = false;
  // variables for fast pulse clock pin timing from StartStop
  int pulseClockPins[16];
  int numPulseClockPins = 0;
  // krakenVars::debugLevel can be overriden to 1 in Config.h
  int debugLevel = 0;
}

#include "Config.h"

Networker* netw = new Networker(config::controls,  arraySize(config::controls),
                                config::sensors,   arraySize(config::sensors),
                                config::processes, arraySize(config::processes));

//create a pointer to a created debug class instance - arg = 1 for debug, 0 for no debug
#include "_DebugUtils.h"
Debug* debug = new Debug(krakenVars::debugLevel);

LED* ledBuiltIn = new LED(13);

#ifndef DIRECT_MODE
unsigned long millisLastSensoring = 4000000000;
#endif

void setup(){
  ledBuiltIn->shine(true);
}

void loop(){
  debug->resetDebugString();

  for(unsigned int proc=0; proc<arraySize(config::processes); proc++){
    config::processes[proc]->step();
  }

  #ifndef DIRECT_MODE
  // read the sensor every millisecond and if the values change add them to the sensor's history
  if (millisSinceSync != millisLastSensoring){
    millisLastSensoring = millisSinceSync;
    for(int sens=0; sens<netw->numSensors; sens++){
      config::sensors[sens]->read();
    }
    for(int sens=0; sens<netw->numSensors; sens++){
      Sensor* sensor = config::sensors[sens];
      bool different = false;
      for(int b=0; b<sensor->numSensBytes; b++){
        if (sensor->sensBytes[b] !=sensor->lastSensedBytes[b]){
          different = true;
        }
      }
      if (different){
        // update the history and the most recent value with the new data
        for(int b=0; b<sensor->numSensBytes; b++){
         sensor->historyBytes[sensor->lenHistory][b] =sensor->sensBytes[b];
         sensor->lastSensedBytes[b] =sensor->sensBytes[b];
        }
        longToBytes(sensor->historyMillis[sensor->lenHistory], millisSinceSync);
        if (krakenVars::active){
         sensor->lenHistory = min(sensor->lenHistory +1, 1023);
        } else {
          // otherwise just keep this one datapoint alive. Incrementing with nobody to read and reset would crash the code. 
         sensor->lenHistory = 1;
        }
      }
    }
  }
  #endif
  
  if(Serial.available()>=netw->READBUFFERSIZE){
    for(int i=0; i<netw->READBUFFERSIZE; i++){
      netw->readBuf[i] = Serial.read();
    }
    //The message is now within the array readBuf

    static char receivedmsg[] = "Teensy Received bytes: ";
    debug->debugStr(receivedmsg);
    static char debugReceived[] = "B%i: %x ";
    for(int i=0; i<netw->READBUFFERSIZE; i++){
      debug->debugIntByte(debugReceived, i, netw->readBuf[i]);
    }

    //------------DISTRIBUTE READBUFFER BYTES TO THE CONTROL DEVICES DATA------------
    netw->currentBufferByte = 0;
    for(int contr=0; contr<netw->numControls; contr++){
      for(int by=0; by<config::controls[contr]->numCtrlBytes; by++){
        config::controls[contr]->ctrlBytes[by] = netw->readBuf[netw->currentBufferByte];
        netw->currentBufferByte++;
      }
    }

    //------------RUN CONTROL DEVICES WITH THEIR RECEIVED COMMANDS------------
    for(int contr=0; contr<netw->numControls; contr++){
      config::controls[contr]->act();
    }

    // example code to show the first controlled device's first byte on the display
    // display->showArdString(String(config::controls[0]->data[0]));

    //------------CONFIRM COMPLETION OF READING------------
    testForLeftoverSerialIn();

    //------------PREVENT UNSIGNED LONG elapsedMicros OVERFLOW AFTER 1Hr11Mins------------
    if(microsSinceHour >= 3600000000){
      microsSinceHour -= 3600000000;
      //elapsedMillis is an unsigned long => it will roll over after 49.7 days
    }

    #ifdef DIRECT_MODE
      //------------COLLECT NEW DATA------------
      for(int sens=0; sens<netw->numSensors; sens++){
        config::sensors[sens]->read();
      }

      //------------SEND LEADING MESSAGE LENGTH BYTE------------
      Serial.write(netw->MESSAGELENGTH);

      //------------FILL UP THE MESSAGE TO BE SEND WITH SENSOR READINGS------------
      netw->currentSendByte = 0;
      for(int sens=0; sens<netw->numSensors; sens++){
        for(int by=0; by<config::sensors[sens]->numSensBytes; by++){
          netw->message[netw->currentSendByte] = config::sensors[sens]->sensBytes[by];
          // config::controls[contr]->ctrlBytes[by] = netw->readBuf[netw->currentBufferByte];
          netw->currentSendByte++;
        }
      }
      
      //------------SEND THE READINGS------------
      for(int i=0; i<netw->MESSAGELENGTH; i++){
        Serial.write(netw->message[i]);
      }
    #endif

    #ifndef DIRECT_MODE
      //------------SEND THE DENSE LOG------------
      int historyLength = 0;
      byte historyLengthBytes[2] = {0x00, 0x00};
      for(int sens=0; sens<netw->numSensors; sens++){
        Sensor* sensor = config::sensors[sens];
        // messageLength += sensor->numSensBytes * sensor->lenHistory  // values
        //                  + 4 * sensor->lenHistory;                                 // timestamps
        historyLength = sensor->lenHistory;
        // the python side knows the byte_length and thus how much data this corresponds to
        historyLengthBytes[0] = historyLength & 0xFF;
        historyLengthBytes[1] = (historyLength >> 8) & 0xFF;
        Serial.write(historyLengthBytes, 2);

        for(int entry=0; entry<sensor->lenHistory; entry++){
          Serial.write(sensor->historyMillis[entry], 4); // timestamps
        }
        for(int entry=0; entry<sensor->lenHistory; entry++){
          Serial.write(sensor->historyBytes[entry], sensor->numSensBytes); //values
        }

        sensor->lenHistory = 0;
      }
    #endif
    
    //------------IF DEBUG: SERIAL WRITE DEBUG INFORMATION------------
    debug->serialWriteDebug();

    //------------SEND THE USB PACKAGE IF IT WASN'T ALREADY SENT------------
    Serial.send_now();
  }
  
  // You can use the display to show arduino strings during development 
  // String exampleString = String("example string, " + String(netw->readBuf[2]));
  // display->showArdString(String(exampleString));
  // display->showTime(millisSinceSync, microsSinceHour);
}

void testForLeftoverSerialIn(){
  // If there are any input bytes leftover before resuming communication;
  // remove them and turn off the LED to indicate an encountered issue
  while(Serial.available()>0){
    Serial.read();
    ledBuiltIn->shine(false);
    static char debugLeftover[] = "A leftover input byte was found\n";   debug->debugStr(debugLeftover);    
  }
}

