#define arraySize(arr) (sizeof(arr)/sizeof((arr)[0]))
// The size of a teensy *pointer is 4 byte => cannot sizeof(ArrPointer) inside function/class

elapsedMillis millisSinceSync;
elapsedMicros microsSinceHour;

//-----------SERIAL ID FOR USB------------
// Provides a serial number "KRAKEN000" that can be found by the python networker.
// If issues occur as a result of multiple connected devices with identical serial numbers,
// simply change the serial number, i.e. to {'K', 'R', 'A','K', 'E', 'N', '1', '2', '3', 0},
extern "C"
{
    struct usb_string_descriptor_struct
    {
        uint8_t bLength;
        uint8_t bDescriptorType;
        uint16_t wString[10];
    };

      usb_string_descriptor_struct usb_string_serial_number =
      {
          22,  // 2 + 2*length of the serial number string
          3,
          {'K', 'R', 'A', 'K', 'E', 'N', '0', '0', '0', 0},
      };
}

void longToBytes(byte* byteArr, long l){
  //This function will fill the byte array at the provided pointer
  //with the bytes of the provided long variable
  byteArr[0] = l & 0xFF;         // get the 8 bit at the end = part that overlaps (&) with 000000FF
  byteArr[1] = (l >> 8) & 0xFF;  // shift these 8 bit into oblivion and get the next 8
  byteArr[2] = (l >> 16) & 0xFF; // least significant byte first => little endian ordering
  byteArr[3] = (l >> 24) & 0xFF; // arduino variables are little endian by default
}

long bytesToULong(byte* b, bool bigEndian){
  // the example 2 byte array byte myByteArr[4] {0, 0, 0x03, 0xed}; in big endian would be 3x256+237 = 1005
  // the little endian array would be {0xed, 0x03, 0, 0}
  // myByteArr = {readBuf[currentBufferByte], readBuf[currentBufferByte+1], 0, 0};
  unsigned long l;
  if (bigEndian){
    l = 256*256*256*b[0] + 256*256*b[1] + 256*b[2] + b[3];
  } else {
    // little endian
    l = b[0] + 256*b[1] + 256*256*b[2] + 256*256*256*b[3];
  }
  return l;
  // an example usage to receive a 2 byte number (<65_536) within your code could look like this:
  // byte longArr[4];
  // longArr[0] = readBuf[currentBufferByte];
  // longArr[1] = readBuf[currentBufferByte+1];
  // longArr[2] = 0;
  // longArr[3] = 0;
  // long a = bytesToULong(longArr, false);
}

class LED{
  private:
    int ledPin;

  public:
    LED(int ledPin_){
      ledPin = ledPin_;
      pinMode(ledPin, OUTPUT);
    }

    void shine(bool on){
      on ? digitalWrite(ledPin, HIGH) : digitalWrite(ledPin, LOW);
    }
};