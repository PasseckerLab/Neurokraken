// set up a usb identifier with the name PULSETEST
extern "C"
{    struct usb_string_descriptor_struct
    {   uint8_t bLength;        uint8_t bDescriptorType;        uint16_t wString[10];    };

      usb_string_descriptor_struct usb_string_serial_number =
      {          22,          3,          {'P', 'U', 'L', 'S', 'E', 'T', 'E', 'S', 'T', 0},      };
}

elapsedMillis ms;
elapsedMicros us;

bool started = false;
bool clockState = true;
int clockPin = 1;
byte sendingMS[] = {0x00, 0x00, 0x00, 0x00};
byte sendingUS[] = {0x00, 0x00, 0x00, 0x00};

void setup() {
  pinMode(3, INPUT);
  pinMode(13, OUTPUT); // built-in LED
}

void loop() {
  bool current = digitalRead(clockPin);
  digitalWrite(13, current);
  if(current != clockState){
    clockState = current;
    longToBytes(sendingMS, ms);
    for(int i=0; i<4; i++){
      Serial.write(sendingMS[i]);
    }
    longToBytes(sendingUS, us);
    for(int i=0; i<4; i++){
      Serial.write(sendingUS[i]);
    }
    Serial.send_now();
  }
}

void longToBytes(byte* byteArr, long l){
  byteArr[0] = l & 0xFF;        
  byteArr[1] = (l >> 8) & 0xFF; 
  byteArr[2] = (l >> 16) & 0xFF;
  byteArr[3] = (l >> 24) & 0xFF;
}