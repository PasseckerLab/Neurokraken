#include <PWMServo.h>

class ServoMotor : public Control {
private:
    int servoPin;
    PWMServo pwmServo_;
    unsigned int position;
    unsigned int lastPosition;

public:
    ServoMotor(int servoPin_) : servoPin(servoPin_), position(90), lastPosition(90) {
        pwmServo_.attach(servoPin_);
    }

    void act() {
        position = intFromByte();
        if (position != lastPosition) {
            pwmServo_.write(position);
            lastPosition = position;
        }
    }
};