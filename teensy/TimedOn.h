// Example corresponding python serial_out entry:
//
//  'reward_valve': {'value': 0, 'encoding': 'uint', 'byte_length': 2,
//                   'default': 0, 'reset_after_send': True},
//
// Example python usage:
//   get.send_serial('reward_valve', 60)


class TimedOn : public Control, public Process{
  // 2 bytes => 65_536 ms maximum open duration
  public:
    int pin;
    bool open;
    uint time = 0;
    unsigned long startTime;;

    TimedOn(int pin_){
      numCtrlBytes = 2;
      pin = pin_;
      pinMode(pin, OUTPUT);
      open = false;
      startTime = 0;
    }

    void act(){
      if(!open){
        time = intFrom2Bytes();
        if(time != 0){
          open = true;
          startTime = millisSinceSync;
          digitalWrite(pin, HIGH);
        }
      } 
    }

    void step(){
      if (open){
        if (millisSinceSync - startTime > time){
          open = false;
          digitalWrite(pin, LOW);
        }
      }
    }
};
