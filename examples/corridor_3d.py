from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in = {
    'walking_pos': devices.rotary_encoder(pins=(31, 32), keys=['down', 'up'])
}

serial_out = {
    'reward_valve':   devices.timed_on(pin=40),
}

display = Display(size=(800,600), renderer='P3D')  # ! Important to set the renderer to P3D for 3D

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, 
                 display=display, mode='keyboard')

from neurokraken.controls import get
from pathlib import Path
import numpy as np

class Corridor(State):
    def on_start(self):
        # get the encoder position at the start of the state. All our movements will be calculated as
        # relative to this starting position. 
        self.steering_scale = 0.025
        self.last_position = get.read_in('walking_pos')
        self.position = 465

        self.recent_deltas = [0] * 50
        self.last_speed_check = get.time_ms
        self.received_reward = False
        
    def loop_main(self):
        new_position = get.read_in('walking_pos')
        delta = new_position - self.last_position
        # update the current position for the next loop iteration now that you have the delta
        self.last_position = new_position
        # scale the delta for the task
        delta *= self.steering_scale
        self.position += delta
        # prevent walking backwards out of the world
        self.position = max(465, self.position)

        if self.last_speed_check + 10 < get.time_ms:
            self.last_speed_check = get.time_ms
            self.recent_deltas.pop(0)
            self.recent_deltas.append(delta)
    
        if self.position > 545 and self.position < 585:
            if np.sum(np.abs(self.recent_deltas)) < 0.1 and not self.received_reward:
                get.send_out('reward_valve', 80)
                self.received_reward = True

        if self.position >= 660:
            # the end was reached, go on to the next trial
            return True, 0

        return False, 0

    def loop_visual(self, sketch):
        sketch.background(0, 0, 40)

        # set the camera field of view (these methods are documented in the py5 documentation)
        sketch.perspective(1, sketch.width/sketch.height, 0.01, 1000)
 
        sketch.lights()
        # move to the current position (here the only change is in the z-axis)
        sketch.translate(sketch.width/2, sketch.height/2, self.position)
        # add light from the top back
        sketch.directional_light(126, 126, 126, 1, 1, 1)
        sketch.directional_light(126, 126, 126, -1, -1, 1)
        # show the world
        sketch.shape(self.world)
         
    def pre_task(self, sketch):
        # assets needs to be loaded before other functions that might need them
        filepath = str((Path(__file__).parent / 'assets' / 'corridor.obj').resolve())
        self.world = sketch.load_shape(filepath)
        # py5 uses a left hand coordinate system mirrored from blender's right hand system => flip the x axis
        self.world.scale(-1,1,1)
        
#------------------------- TASK PROTOCOL BLOCKS AND BLOCK TRIAL STATES -------------------------

task  = {
'corridor': Corridor(max_time_s=1_000_000, next_state='corridor')
}

nk.load_task(task)

nk.run()
