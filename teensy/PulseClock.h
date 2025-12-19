// Example corresponding python serial_out entry:
//
// 'clock_100ms': {'value': 0, 'encoding': 'uint', 'byte_length': 1, 'logging':True,
//                 'arduinoClass': 'PulseClock', 'arduino_args': [<pin>, <change_periods_ms>]}

class PulseClock : public Sensor, public Process{
  public:
    int pin;
    unsigned int changePeriodsMillis;
    byte currentStateByte;

    PulseClock(int pin_, unsigned int changePeriodsMillis_){
      pin = pin_;
      changePeriodsMillis = changePeriodsMillis_;
      pinMode(pin, OUTPUT);
      digitalWrite(pin, HIGH);
      currentStateByte = 0x01;
      
      // The PulseClock fills a special global reference (pulseClockPins and numPulseClockPins)
      // with its pin information, so that the StartStop control can directly and fast
      // activate/deactivate pins upon a start/stop event
      krakenVars::pulseClockPins[krakenVars::numPulseClockPins] = pin;
      krakenVars::numPulseClockPins++;
    }

    void step(){
      // update the clock signal
      if (krakenVars::active){
        if (millisSinceSync % (changePeriodsMillis * 2) >= changePeriodsMillis){
          // example: 250ms % 100*2 = 50ms !> 100ms,    350ms % 100*2 = 150ms > 100ms
          digitalWrite(pin, HIGH);
          currentStateByte = 0x01;
        } else {
          digitalWrite(pin, LOW);
          currentStateByte = 0x00;
        }
      }
    }

    void read(){
      sensBytes[0] = currentStateByte;
    }
};