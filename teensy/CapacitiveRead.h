// https://www.pjrc.com/teensy/td_libs_CapacitiveSensor.html
// connect your send pin to a high resistance, i.e. 1MOhm, from there to the capacitive 
// object, then further connect the object through 1kOhm back to the sensPin/receivePin

#include <CapacitiveSensor.h>

class CapacitiveRead : public Sensor{
  public:
    int sendPin;
    int sensPin;
    CapacitiveSensor capSens;

    // CapacitiveRead(int sendPin_, int sensPin_){
    CapacitiveRead(int sendPin_, int sensPin_) : capSens(sendPin_, sensPin_){
      sendPin=sendPin_; // 1MOhm
      sensPin=sensPin_; // 1kOhm
      numSensBytes = 4;
    }

    void read(){
      long value = capSens.capacitiveSensor(30);
      longToBytes(value);
    }
};