from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in  = {'LR': devices.analog_read(pin=14, keys=['left', 'right']),
              'UD': devices.analog_read(pin=15, keys=['down', 'up'])}

serial_out = {'reward': devices.timed_on(pin=40)}

nk = Neurokraken(serial_in, serial_out, display=Display(size=(800, 600)), mode='keyboard')

from pathlib import Path
import random
from neurokraken.controls import get
from neurokraken.tools import Millis
millis_timer = Millis()

spawn_points = [[100, 100], [700, 100], [100, 500], [700, 500]]

def constrain(value, minimum, maximum):
    return min(max(value, minimum), maximum)

def distance(x0, y0, x1, y1):
    return ( (x0-x1)**2 + (y0-y1)**2 )**0.5

class Game(State):
    def pre_task(self, sketch):
        # the texture should be loaded before other functions might need it
        assets_path = Path(__file__).parent / 'assets'
        self.text_droplet = sketch.load_image( str(assets_path / 'game_droplet.png') )
        self.text_world =   sketch.load_image( str(assets_path / 'game_world.png') )
        self.text_heroAr =  sketch.load_image( str(assets_path / 'game_heroAr.png') )
        self.text_HeroBr =  sketch.load_image( str(assets_path / 'game_heroBr.png') )

    def on_start(self):
        self.x = 400
        self.y = 300
        self.speed = 10
        self.delta_x = 0 # loop_visual relies on having a self.delta_x from the start on
        self.reward_pos = spawn_points[0]

    def loop_main(self):
        # run game loop calculations at a 60 fps framerate
        if millis_timer() < 16:
            return False, 0
        millis_timer.zero()

        # go from range 0-1024 into -1 to +1
        self.delta_x = (get.read_in('LR') / 512) - 1.0
        self.delta_y = (get.read_in('UD') / 512) - 1.0
        
        # multiply with speed, flip the y axis, update the position
        self.delta_x *= self.speed
        self.delta_y *= self.speed * -1
        self.x += self.delta_x
        self.y += self.delta_y
        self.x = constrain(self.x, 0, 800)
        self.y = constrain(self.y, 0, 600)

        if distance(self.x, self.y, self.reward_pos[0], self.reward_pos[1]) < 130:
            get.send_out('reward', 100)
            spawn_options = [s for s in spawn_points if distance(self.x, self.y, s[0], s[1]) > 250]
            self.reward_pos = random.choice(spawn_options)

        return False, 0

    def loop_visual(self, sketch):
        sketch.background(0)
        sketch.image_mode(sketch.CORNERS)
        sketch.image(self.text_world, 0, 0, 800, 600)

        sketch.image_mode(sketch.CENTER)
        sketch.image(self.text_droplet, self.reward_pos[0], self.reward_pos[1], 200, 200)

        with sketch.push():
            # translate to relative coordinates around the character position
            sketch.translate(self.x, self.y)
            if self.delta_x < 0:
                sketch.scale(-1, 1)      # flip the image
            if get.time_ms % 1000 > 500: # change the texture every 500ms to animate the avatar
                sketch.image(self.text_heroAr, 0, 0, 105, 126)
            else:
                sketch.image(self.text_HeroBr, 0, 0, 105, 126)

task = {
    'game': Game(next_state='game')
}

nk.load_task(task)

nk.run()