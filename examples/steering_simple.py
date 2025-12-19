from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in = {
    'steering_wheel': devices.rotary_encoder(pins=(31, 32), keys=['left', 'right'])
}

serial_out = {
    'reward_valve':   devices.timed_on(pin=40),
}

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out,
                 display=Display(size=(800, 600)), mode='keyboard')

#----------------------------------- TASK -----------------------------------

from neurokraken.controls import get
import random

good_side = random.choice(['left', 'right'])
background_color = (0, 0, 0)
steering_scaling = 0.3

class Delay(State):
    def loop_visual(self, sketch):
        global background_color
        sketch.background(*background_color)

class Steer(State):
    def on_start(self):
        # get the encoder position at the start of the state.
        # All our movements will be calculated as relative to this starting position. 
        self.last_position = get.read_in('steering_wheel')
        self.position = 400
        
    def loop_main(self):
        global steering_scaling, good_side, background_color
        new_position = get.read_in('steering_wheel')
        delta = new_position - self.last_position
        delta *= steering_scaling
        self.position += delta
        
        # update the current position for the next loop iteration
        self.last_position = new_position

        background_color = (64, 0, 0)
        if self.position > 700 or self.position < 100:
            # a decision has been steered, if correct provide a reward and override the color used by the delay
            if (self.position > 700 and good_side == 'right') or (self.position < 100 and good_side == 'left'):
                get.send_out('reward_valve', 50)
                background_color = (0, 64, 0)
            return True, 0
        else:
            return False, 0

    def loop_visual(self, sketch):
        sketch.background(0)
        sketch.fill(0, 127, 0)
        sketch.stroke(0, 255, 0)
        sketch.rect_mode(sketch.CENTER)
        sketch.rect(self.position, 300, 100, 300)

last_trial_side_changed = 0
def change_side():
    global last_trial_side_changed, good_side
    if len(get.log['trials']) > last_trial_side_changed + 5:
        good_side = 'left' if good_side == 'right' else 'right'
        print(f'Changed good side to {good_side}')
        last_trial_side_changed = len(get.log['trials'])

task = {
    'steer':   Steer(max_time_s=30, next_state='waiting'),
    'waiting': Delay(max_time_s=1, next_state='steer', trial_complete=True, run_at_end=change_side)
}

nk.load_task(task)

nk.run()