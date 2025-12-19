#include <Encoder.h>
//https://www.pjrc.com/teensy/td_libs_Encoder.html
//#define ENCODER_OPTIMIZE_INTERRUPTS
//the line above will optimize Encoder.h but cause issue for other uses of interrupts => remove if add other interrupt usage

class RotEnc : public Sensor, public Control{
  public:
    Encoder myEnc;
    long wheelPosition;
    
    //since myEnc would typically be initialized globally, we need to use a constructor like this:
    RotEnc(int A, int B) : myEnc(A, B){
      // overwrite the Sensor class's default byte number
      numSensBytes = 4;
    }
    
    void act(){
      bool resetWheelPos = boolFromByte();
      if(resetWheelPos){
        myEnc.write(0);
      }
    }

    void read(){
      wheelPosition = myEnc.read();
      // calculate the bytes making up the long and store them as sensor data
      // if the encoder were used standalone one could alternatively make a pointer to this long and write() the pointer for 4 bytes length.
      longToBytes(sensBytes, wheelPosition);
    }
};