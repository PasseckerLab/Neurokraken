// Example corresponding python serial_out entry:
//
// 'reward_valve': {'value': False, 'encoding': bool, 'byte_length': 1,
//                  'default': False, 'reset_after_send': True},

class DirectOn : public Control{
  public:
    int pin;

    DirectOn(int pin_){
      pin = pin_;
      pinMode(pin, OUTPUT);
    }

    void act(){
      // You can use functions like boolFromByte() or intFromByte() to get the transmitted value from the networker
      bool open = boolFromByte();
      // Then run your code with the value
      open ? digitalWrite(pin, HIGH) : digitalWrite(pin, LOW);
    }
};
