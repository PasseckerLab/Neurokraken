from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in = {
    'button': devices.binary_read(pin=25, keys=['a'])
}

serial_out = {
    'reward_valve': devices.timed_on(pin=40),
    'beep':         devices.buzzer(pin=26)
}

#---------------------------------- AGENT ----------------------------------

class Agent:
    def __init__(self):
        self.act_freq = 5 # act() will be run 5 times per second
        
        # is pressing a button good in this environment? >0.5 yes, <0.5 no.    # ideal matrix
        # 1st dim green/blue/black color, 2nd dim low/high frequency           #     l  h
        self.pressgood_gb_lh = [[0.0, 0.0],                                    # g [[+, -],
                                [0.0, 0.0]]                                    # b  [-, +]]
     
        self.did_press = None
        self.last_env = None
        self.t_last_choice = 0

    def act(self):
        # the agent will make one decision every 4 seconds, and otherwise keep the button unpressed
        if get.time_ms  > self.t_last_choice + 4000:
            # --- learn from the outcome of the last action ---
            if self.did_press is not None:
                log_rewards = get.log['controls']['reward_valve']
                recent_rewards = [l for l in log_rewards if l[0] > get.time_ms - 4100]
                got_rewarded = len(recent_rewards) != 0
                print(f'my last environment, choice, reward: {self.last_env, self.did_press, got_rewarded}')
                # should pressgood for the experienced environment be increased or decreased
                delta = 0
                if self.did_press and got_rewarded:         delta = +0.1
                if self.did_press and not got_rewarded:     delta = -0.1
                if not self.did_press and got_rewarded:     delta = -0.1
                if not self.did_press and not got_rewarded: delta = +0.1
                self.pressgood_gb_lh[self.last_env[0]][self.last_env[1]] += delta
                # Now that we learned from this experience we can set it back to 0
                self.did_press = None
                print('my new choice matrix:', self.pressgood_gb_lh)
            
            # --- act based on the environment and experience ---
            # process the visual and audio into state spaces of 0 or 1 respectively
            color = np.mean(get.frame, axis=(0,1))
            color = 0 if color.tolist() == [0, 255, 0] else 1
            audio = 0 if get.serial_out['beep']['value'] < 700 else 1
            self.last_env = [color, audio]
            
            # look up experience whether in this environment a button press is good and do the learned button action
            press_good = True if self.pressgood_gb_lh[color][audio] > 0.0 else False
            if press_good == True:
                print(f'Observation: {self.last_env} - I am pressing the button')
                get.serial_in['button']['value'] = True
                self.did_press = True
            else:
                print(f'Observation: {self.last_env} - I am waiting out this stimulus')
                self.did_press = False
            
            self.t_last_choice = get.time_ms
        else:
            get.serial_in['button']['value'] = False

agent = Agent()

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir='./',
                 display=Display(size=(800, 600)), mode='agent', agent=agent)

#----------------------------------- TASK -----------------------------------

from neurokraken.controls import get
import random
import threading, winsound
import numpy as np

# create a numpy array to store the current frame for the agent
get.frame = np.zeros(shape=(800, 600, 3), dtype=np.uint8)

class Choice(State):
    def on_start(self):
        self.color = random.choice(['green', 'blue'])
        self.frequency = random.choice([600, 1200])
        self.start_t = get.time_ms
        self.button_was_pressed = False
        threading.Thread(target=lambda: winsound.Beep(self.frequency, 2000)).start()
    
    def loop_main(self):
        get.send_out('beep', self.frequency)
        # color and tone form 2x2 combinations. 2 combinations will reward pressing the button during
        # the 4s state and 2 combinations (green+low, blue+high) will reward waiting out the 4s
        # without pressing it
        if not self.button_was_pressed:
            if get.read_in('button'):
                if (self.color == 'green' and self.frequency ==  600) or \
                    (self.color == 'blue'  and self.frequency == 1200):
                    print('---REWARD---')
                    get.send_out('reward_valve', 40)
                self.button_was_pressed = True
        if get.time_ms - self.start_t > 3900:
            if not self.button_was_pressed:
                if (self.color == 'green' and self.frequency == 1200) or \
                    (self.color == 'blue'  and self.frequency ==  600):
                    print('---REWARD---')
                    get.send_out('reward_valve', 40)
            return True, 0
        return False, 0
    
    def loop_visual(self, sketch):
        if self.color == 'blue':
            sketch.background(0, 0, 255)
        if self.color == 'green':
            sketch.background(0, 255, 0)
        # update the frame data
        get.frame = sketch.get_np_pixels(bands='RGB')

task = {
    'choice': Choice(max_time_s=4, next_state='choice'),
}

nk.load_task(task)

nk.run()