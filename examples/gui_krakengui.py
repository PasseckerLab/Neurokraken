from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices
from neurokraken.controls import get
import py5 # for py5's noise function to drive our agent's actions

serial_in = {'steering_wheel': devices.rotary_encoder(pins=(31, 32), keys=['left', 'right'])}
serial_out = {'reward': devices.timed_on(pin=40)}

class Agent:
    def __init__(self):
        self.act_freq = 100 # 100hz
      
    def act(self):
        # noise provides a series of random steering positions we can scale to the wheel range
        get.serial_in['steering_wheel']['value'] = (py5.noise(get.time_ms / 1000) - 0.5) * 400 

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, 
                 display=Display(size=(800, 600)), agent=Agent(), mode='agent')

# Task

get.colored_red = False # button controlled 
get.log['notes'] = []   # text field controlled
get.reward_size = 50    # slider controlled
get.log['history'] = [] # log of rewarded reached sides

class Steer_alternating(State):
    def on_start(self):
        self.target_right = True
        self.position = 0
    
    def loop_main(self):
        self.position = get.read_in('steering_wheel') # for this task the range is physically limited [-150, 150]
        reached = None
        if self.target_right and self.position > 90:
            reached = 'right'
        elif not self.target_right and self.position < -90:
            reached = 'left'
        if reached is not None:
            self.target_right = not self.target_right
            get.log['history'].append([get.time_ms, reached])
            get.send_out('reward', get.reward_size)
        return False, 0
    
    def loop_visual(self, sketch):
        sketch.background(0)
        pos_in_visual = sketch.remap(self.position, -150, 150, 0, 800)
        sketch.rect_mode(sketch.CENTER)
        if get.colored_red:
            sketch.fill(255, 0, 0)
        else:
            sketch.fill(0, 255, 255)
        sketch.rect(pos_in_visual, 300, 50, 50)
        sketch.stroke(255)
        if self.target_right:
            sketch.line(640, 0, 640, 600)
        else:
            sketch.line(160, 0, 160, 600)

task = {'steer': Steer_alternating(next_state='steer')}

nk.load_task(task)

# UI-called functions

def change_color():
    get.colored_red = not get.colored_red

def change_reward_size(value):
    get.reward_size = int(min(max(value, 0), 100))
    print(f'updated reward to {get.reward_size}')

def add_note(text):
    print(f'adding timestamped note: {text} to the log')
    get.log['notes'].append([get.time_ms, text])

# UI

from py5 import Sketch
import krakengui as gui

class UI(Sketch):
    def settings(self):
        self.size(400, 400)

    def setup(self):
        with gui.Col(pos=(20, 20)) as col:
            col.add(gui.Button(label='switch color', on_click=change_color))
            col.add(gui.Slider(label='reward size', min=0, max=100, value=50, on_change=change_reward_size))
            col.add(gui.Text_Input(label='add note to log', on_enter=add_note))

        self.last_plot_time = -4000
        self.plot_image = self.create_image(350, 200, self.RGB)

    def draw(self):
        self.background(0)
        if get.quitting:
            self.exit_sketch()

        self.image(self.plot_image, 20, 180)

        # update the plot every 5 seconds
        if get.time_ms - self.last_plot_time > 5_000:
            self.last_plot_time = get.time_ms
            # plot steering
            # only plot the recent time and save some compute by only checking every 3rd entry
            recent_steerings = [entry for entry in get.log['steering_wheel'][::3] if entry[0] > get.time_ms - 40_000]
            times, values = list(zip(*recent_steerings))
            times = [t / 1000 for t in times]
            plt = gui.Plot(w=350, h=200, sketch=self, x=0, y=0)
            plt.plot(times, values)

            # plot reached sides if sides have been reached
            recent_reached = [entry for entry in get.log['history'] if entry[0] > get.time_ms - 40_000]
            if len(recent_reached) != 0:
                times, sides = list(zip(*recent_reached))
                times = [t / 1000 for t in times]
                colors = [(0,255,255) if side=='left' else (255,0,255) for side in sides]
                plt.scatter(xs=times, ys=sides, color=colors, diameter=12, y_axis=1, order=['right', 'left'])
            self.plot_image = plt.show(to_py5image=True, xlabel='t_seconds', ylabel='position')        

    def key_pressed(self, e): pass # a minimal key_pressed function is required for krakengui's text input to work properly

    def exiting(self):
        get.quit()

ui = UI()
ui.run_sketch(block=False)

nk.run()