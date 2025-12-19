class Debug{
  public:
    int debugLevel;
    char debugString[300];
    //create a buffer with sufficient space for the string created by snprintf
    char debugSnprintfBuffer[200];

    Debug(int debugLevel_){
      //level 0: no debug, level 1: all debug information
      debugLevel = debugLevel_;
    }

    void resetDebugString(){
      //start with an empty debugString => direct null termination
      debugString[0] = 0x00;
    }

    void exampleDebug(){
      if(debugLevel == 1){
        //------------PROVIDE DEBUG INFORMATION EXAMPLE------------
        long l = -1234567890;
        byte b = 0xa0;
        float f = 3.14;
        //create a string and put it in the buffer debugSnprintfBuffer, using the maximal 
        //buffer size 200 characters
        snprintf(debugSnprintfBuffer, 200, 
                 "long: %ld, byte: %x, float: %f", l, b, f);
        //concatenate the snprintf string to the debugString
        strlcat(debugString, debugSnprintfBuffer, sizeof(debugString));
        //long: -1234567890, byte: a0, float: 3.140000
        //see https://cplusplus.com/reference/cstdio/printf/ for further specifier characters
      }
    }

    void debugStr(char* cstr){
      if(debugLevel == 1){
        strlcat(debugString, cstr, sizeof(debugString));
      }
    }

    void debugByte(char* cstr, byte b){
      if(debugLevel == 1){
        //use %x within the c string to insert the provided byte
        snprintf(debugSnprintfBuffer, 200, cstr, b);
        strlcat(debugString, debugSnprintfBuffer, sizeof(debugString));
      }
    }

    void debugLong(char* cstr, long l){
      if(debugLevel == 1){
        //use %ld within the c string to insert the provided long
        snprintf(debugSnprintfBuffer, 200, cstr, l);
        strlcat(debugString, debugSnprintfBuffer, sizeof(debugString));
      }
    }

    void debugFloat(char* cstr, float f){
      if(debugLevel == 1){
        //use %f within the c string to insert the provided float
        snprintf(debugSnprintfBuffer, 200, cstr, f);
        strlcat(debugString, debugSnprintfBuffer, sizeof(debugString));
      }
    }

    void debugInt(char* cstr, int i){
      if(debugLevel == 1){
        //use %i within the c string to insert the provided int
        snprintf(debugSnprintfBuffer, 200, cstr, i);
        strlcat(debugString, debugSnprintfBuffer, sizeof(debugString));
      }
    }

    void debugIntByte(char* cstr, int i, byte b){
      if(debugLevel == 1){
        //use %i and %x within the c string to insert the provided int and byte
        snprintf(debugSnprintfBuffer, sizeof(debugSnprintfBuffer), cstr, i, b);
        strlcat(debugString, debugSnprintfBuffer, sizeof(debugString));
      }
    }

    void serialWriteDebug(){
      if(debugLevel == 1){
        Serial.write(strlen(debugString));
        Serial.write(debugString, strlen(debugString));
      }
    }
};
