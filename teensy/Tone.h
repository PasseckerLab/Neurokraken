// Example corresponding python serial_out entry:
//
//  'frequency': {'value': 0, 'encoding': 'uint', 'byte_length': 2,
//                'default': 0, 'reset_after_send': False}
//
// Example python usage:
//   get.send_serial('frequency', 500)


class Tone : public Control{
  // 2 bytes => 65_536 ms maximum frequency
  public:
    int pin;
    int frequency = 0;

    Tone(int pin_){
      numCtrlBytes = 2;
      pin = pin_;
      pinMode(pin, OUTPUT);
    }

    void act(){
      frequency = intFrom2Bytes();
      if(frequency==0){
        noTone(pin);
      } else {
        tone(pin, frequency);
      }
    }
};
