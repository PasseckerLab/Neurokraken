class StartStop : public Control{
  public:
    StartStop(){
    }

    void act(){
      int startStop = intFromByte();
      // 0 = continue as before, 1 = resetAndStart, 2 = stop
      // The python side
      // only lets startStop be 1 if the setup is not already active and
      // only lets startStop be 2 if the setup is not already inactive
      // krakenVars::active is a global variable accessed by the main loop and pulse clock
      if(startStop == 1){
        // reset the clocks to 0
        millisSinceSync = 0;  // reset time value
        microsSinceHour = 0;
        // note that the first millisecond transition will happen within <1ms because 
        // tick timing remains unchanged
        
        // start the clock
        krakenVars::active = true;
        
        // If a pulse clock is used, directly change its pins
        for (int i=0; i<krakenVars::numPulseClockPins; i++){
          digitalWrite(krakenVars::pulseClockPins[i], LOW);
        }
      }
      if(startStop == 2){
        // stop the clock
        krakenVars::active = false;

        // If a pulse clock is used, directly change its pins
        for (int i=0; i<krakenVars::numPulseClockPins; i++){
          digitalWrite(krakenVars::pulseClockPins[i], HIGH);
        }
      }
    }
};