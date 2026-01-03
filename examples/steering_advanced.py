from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in = {
    'clock_100ms':    devices.pulse_clock(pin=2, change_periods_ms= 100),
    'clock_1s':       devices.pulse_clock(pin=3, change_periods_ms=1000),
    'steering_wheel': devices.rotary_encoder(pins=(31, 32), keys=['left', 'right'])
}

serial_out = {
    'reward_valve':   devices.timed_on(pin=40),
    'steering_wheel': devices.rotary_encoder(pins=(31, 32), controls=True) # ! same name but controls=True
}

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out,
                 display=Display(size=(800, 600)), mode='keyboard', autostart=False)

import random
from neurokraken.controls import get
from pathlib import Path

#----------------------------------- TASK -----------------------------------

probability_left_spawn = 0.5
valve_open_t_ms = 60
steering_scaling = 0.2

class Delay(State):
    def loop_visual(self, sketch):
        sketch.background(0, 0, 0)

class Timeout(State):        
    def loop_visual(self, sketch):
        sketch.background(64,0,0)

class Reward(State):
    def on_start(self):
        global valve_open_t_ms
        get.send_out('reward_valve', valve_open_t_ms)

    def loop_visual(self, sketch):
        sketch.background(0,64,0)

class Steer(State):
    def on_start(self):
        # get the encoder position at the start of the state. All our movements will be 
        # calculated as relative to this starting position. 
        self.last_position = get.read_in('steering_wheel')

        global probability_left_spawn
        if random.random() < probability_left_spawn:
            get.log['trials'][-1]['side'] = 'l'
            self.position = 200
        else:
            get.log['trials'][-1]['side'] = 'r'
            self.position = 600
        
    def loop_main(self):
        """When the shape was moved more than 200 from its starting position and is at the center,
        the State is completed and will move on to next_state 0. Otherwise if the shape was steered
        to the edge it will move on to next_state 1"""
        global steering_scaling
        new_position = get.read_in('steering_wheel')
        delta = new_position - self.last_position
        delta *= steering_scaling
        self.position += delta
        
        # update the current position for the next loop iteration
        self.last_position = new_position

        if get.log['trials'][-1]['side'] == 'l':
            if self.position > 400:
                return True, 0
            elif self.position < 0:
                return True, 1
        else:
            if self.position < 400:
                return True, 0
            elif self.position > 800:
                return True, 1
        # timeout condition
        return False, 1

    def loop_visual(self, sketch):
        sketch.background(0)
        sketch.image_mode(sketch.CENTER)
        sketch.image(self.texture, self.position, 300, 100, 300)

    def pre_task(self, sketch):
        # the texture should be loaded before other functions might need it
        self.texture = str(Path(__file__).parent / 'assets' / 'steering_texture.png')
        self.texture = sketch.load_image(str(self.texture))
        
#------------------------- SCHEDULE -------------------------

# To schedule task changes we write a function to provide as run_post_trial. (or as the final states' run_at_end=.)
# Checking State's signature for a run_at_end-function it receives a reference to the current state
# and whether it was sucessfully finished (or timed out).
def switch_side_probability_if_performant():
    """Check the recent 5 trials to determine the performance. If the subject 
    performs correctly (rewarded) in more than 75% of the last 5 trials, the probability of the
    stimulus appearing on the left side (probability_left_spawn) is adjusted.
    The adjustment alternates the probability between 0.2 and 0.8."""

    global probability_left_spawn
    n_last_trials = 5
    last_n_trials = get.log['trials'][-n_last_trials:]
    # don't test if too few trials have been performed or a switch already took place recently.
    if len(get.log['trials']) < n_last_trials:
        return
    num_recent_switches = len([t for t in last_n_trials if 'switched_side' in t])
    if num_recent_switches != 0:
        return
    num_rewarded = len([t for t in last_n_trials if 'rewarded' in t]) # added by log_reward() beneath
    ratio_correct = num_rewarded / n_last_trials
    if ratio_correct > 0.75:
        probability_left_spawn = 0.2 if probability_left_spawn > 0.5 else 0.8
        get.log['trials'][-1]['switched_side'] = probability_left_spawn
        print(f'switched to new left spawn probabiltiy: {probability_left_spawn}')

# We can also provide a run_at_start function to states
def log_reward():
    get.log['trials'][-1]['rewarded'] = True

#------------------------- TASK PROTOCOL -------------------------

task = {
    'waiting': Delay(max_time_s=1, next_state='steer'),
    'steer':   Steer(max_time_s=30, next_state=['reward', 'timeout']),
    'reward':  Reward(max_time_s=1, next_state='waiting',
                      run_at_start=log_reward,
                      trial_complete=True),
    'timeout': Timeout(max_time_s=1, next_state='waiting',
                       trial_complete=True)
}

nk.load_task(task, run_post_trial=switch_side_probability_if_performant)

#------------------------- ADD A SMALL UI -------------------------
from py5 import Sketch
import krakengui as gui

def override_reward():
    global valve_open_t_ms
    get.send_out('reward_valve', valve_open_t_ms)

class UI(Sketch):
    def settings(self):
        self.size(500, 200)

    def setup(self):
        self.window_title('UI')
        self.window_move(0,630)
                
        with gui.Col(pos=(270, 10)) as col:
            col.add(gui.Button(label='override single reward',on_click=override_reward))
            col.add(gui.Button(label='start task', on_click=get.start)) # as we set autostart=False we
            col.add(gui.Button(label='stop task', on_click=get.stop))   # have to manually start the task
            def reset_wheel(): get.send_out('steering_wheel', True)
            col.add(gui.Button(label='reset wheel pos', on_click=reset_wheel))

    def draw(self):
        global probability_left_spawn
        self.background(0)
        self.fill(255);     self.stroke(255)
        self.text_size(15)
        # show some general task information, with \n to start newlines
        self.text(f'time (ms): {get.read_in('t_ms')}\n' + 
                  f'wheel pos: {get.read_in('steering_wheel')}\n'
                  f'probability_left_spawn: {probability_left_spawn}\n' +
                  f'number of trials: {len(get.log["trials"])}\n', 10, 25)
        
        if get.quitting:
            self.exit_sketch() # end the UI if the experiment is quitting from its side

    def exiting(self):
        # end the experiment when the UI window is closed
        get.quit()

#------------------------- START THE UI AND TASK -------------------------

ui = UI()
ui.run_sketch(block=False)

nk.run()