from neurokraken import Neurokraken, State
from neurokraken.configurators import devices, Display

serial_in =  {}
serial_out = {'reward_valve': devices.timed_on(pin=2)}

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, mode='keyboard',
                 display=Display(size=(800,600)))

from neurokraken.controls import get

# global variables to be updated throughout the task
get.num_dots = 1000
get.dots = []

import random
import numpy as np

class Dot():
    def __init__(self, mean=3.14159, sd=1, p_teleport=0.1, speed=10, size=12.5):
        self.teleport()
        self.size = random.randint(int(size*0.8), int(size*1.2))
        self.p_teleport = p_teleport
        self.mean, self.sd = mean, sd
        self.speed = speed
        self.redirect()

    def update(self):
        if random.random() < self.p_teleport:
            self.teleport()
        # polar to cartesian (with r=1)
        dx, dy = np.cos(self.angle_movement), np.sin(self.angle_movement)
        dx *= self.speed
        dy *= self.speed
        self.x += dx
        self.y += dy
        if self.x < -50 or self.x > 850 or self.y<-50 or self.y>650:
            self.teleport()
    
    def teleport(self):
        # add a bit more space at the edges
        self.x = random.randint(-50, 850)
        self.y = random.randint(-50, 650)

    def redirect(self, mean=None, sd=None):
        """Update the angle to the provided mean u and standard deviation sd"""
        self.sd = self.sd if sd is None else sd
        self.mean = self.mean if mean is None else mean
        self.angle_movement = np.random.normal(loc=self.mean, scale=self.sd)

    def show(self, sketch):
        sketch.stroke_weight(self.size)
        sketch.point(self.x, self.y)

get.dots = [Dot(mean=3.14159, sd=1.5, p_teleport=0.20) for i in range(get.num_dots)]

class Random_Dots(State):
    def on_start(self):
        # angles: left 0 pi, 2 pi, up 0.5 pi, right 1 pi, down 1.5 pi
        if random.random() < 0.5:
            get.log['trials'][-1]['direction'] = 'right'
            angle = 0 
        else:
            get.log['trials'][-1]['direction'] = 'left'
            angle = 3.14159
        update_angle(angle)

        self.made_choice = False
        self.correct_choice = False

    def loop_main(self):
        if self.made_choice:
            if self.correct_choice:
                return True, 1
            else:
                return True, 0
        return False, 0

    def loop_visual(self, sketch):
        sketch.background(0)
        sketch.stroke(255)
        for dot in get.dots:
            dot.update()
            dot.show(sketch)
        if sketch.is_mouse_pressed:
            # touch screen presses register as mouse clicks
            if sketch.mouse_x < sketch.width/2:
                if get.log['trials'][-1]['direction'] == 'left':
                    self.correct_choice = True
                self.made_choice = True
            if sketch.mouse_x >= sketch.width/2:
                if get.log['trials'][-1]['direction'] == 'right':
                    self.correct_choice = True
                self.made_choice = True

def update_angle(value):
    for dot in get.dots: dot.redirect(mean=value)

def update_SD(value):
    for dot in get.dots: dot.redirect(sd=value)

def update_probab_teleport(value):
    for dot in get.dots: dot.p_teleport = value

def update_size(value):
    for dot in get.dots: dot.size = random.randint(int(value*0.8), int(value*1.2))

def update_number_dots(value):
    get.dots = [Dot() for i in range(int(value))]

def update_speed(value):
    for dot in get.dots: dot.speed = value

class Reward(State):
    def on_start(self):
        get.send_out('reward_valve', 70)
        
    def loop_visual(self, sketch):
        sketch.background(0, 64, 0)


task = {
    'random_dots': Random_Dots(max_time_s=20, next_state=['delay', 'reward']),
    'reward':  Reward(max_time_s=0.3, next_state='random_dots', trial_complete=True),
    'delay': State(max_time_s=0.3, next_state='random_dots', trial_complete=True) # empty minimal state
}

nk.load_task(task)

from py5 import Sketch
import krakengui as gui

#------------------------- UI -------------------------

class UI(Sketch):
    def settings(self):
        self.size(180, 270)

    def setup(self):
        self.window_title('UI')
        self.window_move(800,0)
        
        gui.use_sketch(self)
        
        with gui.Col(pos=(5, 10)) as col:
            col.add(gui.Slider(max=6.28318, on_change=update_angle, 
                               on_change_while_dragged=True, label='angle'))
            col.add(gui.Slider(max=3.14159, value=1, on_change=update_SD, 
                               on_change_while_dragged=True, label='standard deviation'))
            col.add(gui.Slider(max=20, value=500, on_change=update_speed, 
                               on_change_while_dragged=True, label='speed'))  
            col.add(gui.Slider(max=1.0, on_change=update_probab_teleport, value=0.1,
                               on_change_while_dragged=True, label='probability teleport'))
            col.add(gui.Slider(max=30, value=12.5, on_change=update_size, 
                               on_change_while_dragged=True, label='dot_size'))
            col.add(gui.Slider(max=1500, value=500, on_change=update_number_dots, 
                               on_change_while_dragged=True, label='number of dots'))

    def draw(self):
        self.background(0)
        if get.quitting: 
            self.exit_sketch()

    def exiting(self):
        get.quit()

ui = UI()
ui.run_sketch(block=False)

nk.run()
