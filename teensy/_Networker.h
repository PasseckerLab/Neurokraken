class Control{
  public:
    byte ctrlBytes[32];
    int numCtrlBytes = 1;

    virtual void act(){
      // overwrite this function with a void act() in your own class code
    }

    int valueFromBytes(){
      // examples: int i = valueFromBytes();
      //           bool b = valueFromBytes();
      if (numCtrlBytes == 1){
        return int(ctrlBytes[0]);
      }
      else if (numCtrlBytes == 2){
        // 2 bytes into a uint 0 to 65,535
        unsigned int value = 0;
        value = ctrlBytes[0] + 256*ctrlBytes[1]; // little endian
        return value;
      }
      return 0;
    }

    // --- legacy non-overloaded functions ---

    bool boolFromByte(){
      return ctrlBytes[0] == 0x01 ? true : false;
    }

    bool boolFromByte(int i){
      return ctrlBytes[i] == 0x01 ? true : false;
    }

    unsigned int intFromByte(){
      return int(ctrlBytes[0]); 
      //1 byte => 0 to 255 - byte is inherently unsigned, 0x00=0, 0xff=255
    }

    unsigned int intFromByte(int i){
      return int(ctrlBytes[i]); 
    }

    unsigned int intFrom2Bytes(){
      // 2 bytes into a uint 0 to 65,535
      unsigned int value = 0;
      value = ctrlBytes[0] + 256*ctrlBytes[1]; // little endian
      return value;
    } 
};

class Sensor{
  public:
    byte sensBytes[32];
    int numSensBytes = 1;


    #ifndef DIRECT_MODE
    int lenHistory = 0;
    int numValues = 1; // currently unused variable
    // start with a default max of 12 sensBytes so the history has sufficient space.
    // (use a lower default if memory size becomes an issue) 
    // The history keeps track of up to 1024 yet uncommunicated datapoints
    byte historyBytes[1024][12];
    byte historyMillis[1024][4];
    byte lastSensedBytes[32] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    #endif

    virtual void read(){
      // overwrite this function with a void read() in your own class code that fills up sensBytes[] with what you want to send
    }

    void valueToBytes(int i){
      // examples: int i = 10;
      //           valueToBytes(i);
      if (numSensBytes == 1){
        sensBytes[0] = i & 0xFF;
      }
      else if (numSensBytes == 2){
        sensBytes[0] = i & 0xFF;
        sensBytes[1] = (i >> 8) & 0xFF;
      }
    }

    void valueToBytes(long l){
      // 4 sensBytes
      sensBytes[0] = l & 0xFF;
      sensBytes[1] = (l >> 8) & 0xFF;
      sensBytes[2] = (l >> 16) & 0xFF;
      sensBytes[3] = (l >> 24) & 0xFF;
    }

    // --- legacy non-overloaded functions ---

    void int8ToByte(byte* byteArr, int i){
      // int values 0 to 255 can be stored in a single byte
      byteArr[0] = i & 0xFF; 
      // same as byte(i) or unsigned char(i);
    }

    void int16ToBytes(byte* byteArr, int i){
      // turn a 2 byte int (0 to 65535) into 2 bytes.
      // This is relevant for values from analogRead() which are in the range of 0-1024
      // (teensy4.1 could even support 12bit resolution) whereas a single byte can only hold a 8 bit range of 0-255
      byteArr[0] = i & 0xFF;
      byteArr[1] = (i >> 8) & 0xFF;
    }
    
    void longToBytes(byte* byteArr, long l){
      // This function will fill the byte array at the provided pointer
      // with the bytes of the provided long variable
      byteArr[0] = l & 0xFF;         // get the 8 bit at the end = part that overlaps (&) with 000000FF
      byteArr[1] = (l >> 8) & 0xFF;  // shift these 8 bit into oblivion and get the next 8
      byteArr[2] = (l >> 16) & 0xFF; // least significant byte first => little endian ordering
      byteArr[3] = (l >> 24) & 0xFF; // arduino variables are little endian by default
    }
    

    //reading functions
    void int8ToByte(int i){
      sensBytes[0] = i & 0xFF;
    }

    void int16ToBytes(int i){
        sensBytes[0] = i & 0xFF;
        sensBytes[1] = (i >> 8) & 0xFF;
    }

    void longToBytes(long l){
      sensBytes[0] = l & 0xFF;
      sensBytes[1] = (l >> 8) & 0xFF;
      sensBytes[2] = (l >> 16) & 0xFF;
      sensBytes[3] = (l >> 24) & 0xFF;
    }

    void ints8ToBytes(int a, int b){
      sensBytes[0] = a & 0xFF;
      sensBytes[1] = b & 0xFF;
    }
};

class Process{
  public:
    virtual void step(){
        // overwrite this function with a void step() in your own class code that will run every teensy loop() iteration.
        // In the main loop step() will run a lot more frequent than communication-dependent code like a Sensor or 
        // Control's read() or run() and can be used for devices that require very dense continuous signals like motors, or that need 
        // to independently run with the precision of millisSinceSync or microsSinceHour variables, like a syncronization pulse clock.
    }
};

class Networker{
  
  public:
    int READBUFFERSIZE = 0; // total received bytes
    int numControls;        // number of control devices
    byte* readBuf;          // pointer to the array, since we don't know the size yet
    int currentBufferByte = 0;

    int MESSAGELENGTH = 0;
    int numSensors;
    byte* message;
    int currentSendByte = 0;

    int numProcesses = 0;

    Networker(Control** controls, int numControls_, Sensor** sensors, int numSensors_,
              Process** processes, int numProcesses_){
      // ** since controls is a pointer to a pointer (Control* inside the array)
      numControls = numControls_;
      // calculate the readbuffersize
      for(int i=0; i<numControls; i++){
        READBUFFERSIZE += controls[i]->numCtrlBytes;
      }
      readBuf = new byte[READBUFFERSIZE];
    
      numSensors = numSensors_;
      for(int i=0; i<numSensors; i++){
        MESSAGELENGTH += sensors[i]->numSensBytes;
      }
      message = new byte[MESSAGELENGTH];

      numProcesses = numProcesses_;
    }
};