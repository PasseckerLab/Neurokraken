from neurokraken import Neurokraken, State
from neurokraken.configurators import devices

serial_in = {
    'touch_left': devices.capacitive_touch(pins=[10, 11], keys=['a']),
    'touch_right': devices.capacitive_touch(pins=[29, 30], keys=['d'])
}

serial_out = {
    'servo': devices.servo(pin=14),
    'reward_valve': devices.timed_on(pin=40),
}

#---------------------------------- AGENT ----------------------------------

class Agent:
    def __init__(self):
        self.act_freq = 0.5 # act() will be run every 2 seconds

    def act(self):
        if get.serial_out['servo']['value'] == 10:
            print('I am touching the left sensor')
            get.serial_in['touch_left']['value'] = 6000
        elif get.serial_out['servo']['value'] == 245:
            print('I am touching the right sensor')
            get.serial_in['touch_right']['value'] = 6000
        else:
            # not touching either
            get.serial_in['touch_left']['value'] = 0
            get.serial_in['touch_right']['value'] = 0

agent = Agent()

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, mode='agent', agent=agent)

#----------------------------------- TASK -----------------------------------

from neurokraken.controls import get
import random
import numpy as np

# create a numpy array to store the current frame for the agent
get.frame = np.zeros(shape=(800, 600, 3), dtype=np.uint8)

class Intertrial(State):
    def on_start(self):
        get.send_out('servo', 127)                # arm in middle position

class Choice(State):
    def on_start(self):
        self.servo_pos = random.choice([10, 245]) # left or right position
        get.send_out('servo', self.servo_pos)
        print(f'servo as position {self.servo_pos}')
        
    def loop_main(self):
        if self.servo_pos == 10 and get.read_in('touch_left') > 4000:
            get.send_out('reward_valve', 50)
            return True, 0
        elif self.servo_pos == 245 and get.read_in('touch_right') > 4000:
            get.send_out('reward_valve', 50)
            return True, 0
        return False, 0
    
task = {
    'wait': Intertrial(max_time_s=3, next_state='choice'),
    'choice': Choice(max_time_s=15, next_state='wait'),
}

nk.load_task(task)

nk.run()