// code for an adafruit qt py esp32-s3 to create stimului for the teensy as an automated
// replacement for a subject in performance tests.
// The stimuli include:
// 2 servos to create movement for rotary encoders,
// 5 random HIGH/LOW signals as inputs for digitalRead
// It uses a PCA9685 servo driver for convenience
// Requirements: "Adafruit PWM Servo Driver Library by adafruit" for the PCA9685
// https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library
// Note: a new qt-py esp32-s3 can start out stuck in a state where code uploads fail
// until it was once connected and uploaded using a usb-hub.

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

bool servosActive = true;
int servo0pos = 1000;
int servo0Min = 500;
int servo0Max = 1700;
int servo1pos = 1000;
int servo1Min = 500;
int servo1Max = 1700;
int digitalStates[] = {false, false, false, false, false};
int digitalPins[] = {16, 36, 37, 35, 18};



void setup() {
  for (int i=0; i<5; i++){
    pinMode(digitalPins[i], OUTPUT);
  }

  Serial.begin(115200);
  Serial.println("starting stimuli");

  // the used miuzei metal gear micro servos have a pulse width range 500-2500us
  // => pwm cycle is 400hz max for up to 2500us on => use 350 for some breathing room.
  pwm.begin();
  pwm.setPWMFreq(350);
}

void loop() {
  if (servosActive){
    if(random(2500) == 0){
      servo0pos = random(servo0Min, servo0Max);
      pwm.setPWM(0, 0, servo0pos);
    }
    if(random(2500) == 0){
      servo1pos = random(servo1Min, servo1Max);
      pwm.setPWM(1, 0, servo0pos);
    }
  }
  for (int i=0; i<5; i++){
    if(random(500) == 0){
      digitalStates[i] = !digitalStates[i];
      digitalWrite(digitalPins[i], digitalStates[i]);
    }
  } 

  // test for servo functionality and servos on/off:
  while (Serial.available() > 0) {
    digitalWrite(17, HIGH);
    int pos = Serial.readStringUntil('\n').toInt();
    if (pos==0){
      servosActive = false;
    } else if (pos == 1){
      servosActive = true;
    } else {
      Serial.print("seting position to ");
      Serial.println(pos);
      int servoIdx = 0;
      pwm.setPWM(servoIdx, 0, pos); // idx, start_on, start_off on pw time window 0 to 4095
    }
  }
}