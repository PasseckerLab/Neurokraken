class MillisReader : public Sensor{
  public:
    MillisReader(){
      numSensBytes = 4;
    }

    void read(){
      longToBytes(sensBytes, millisSinceSync);
    }
};

class MicrosReader : public Sensor{
  public:
    MicrosReader(){
      numSensBytes = 4;
    }

    void read(){
      longToBytes(sensBytes, microsSinceHour);
    }
};

class AnalogSensor : public Sensor{
  public:
    int pin;

    AnalogSensor(int pin_){
      pin=pin_;
      pinMode(pin, INPUT);
      numSensBytes = 2;
    }

    void read(){
      int value = analogRead(pin);
      int16ToBytes(value);
    }
};

class DigitalSensor : public Sensor{
  public:
    int pin;
    int value;

    DigitalSensor(int pin_): pin(pin_), value(0){
      pinMode(pin, INPUT);
      numSensBytes = 1;
    }

    void read(){
      int value = digitalRead(pin); // 1 True, 0 False
      int8ToByte(value);
    }
};