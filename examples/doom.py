from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in  = {'shoot': devices.binary_read(pin=13, keys=['space']),
              'turn': devices.analog_read(pin=14, keys=['left', 'right']),
              'forward': devices.analog_read(pin=15, keys=['down', 'up'])}

serial_out = {'reward': devices.timed_on(pin=40)}

nk = Neurokraken(serial_in, serial_out, display=Display(size=(800, 600)), mode='keyboard')

import vizdoom as vzd # pip install vizdoom --pre
from neurokraken.controls import get
from neurokraken.tools import Millis
millis_timer = Millis()

import numpy as np

get.fps = 60
game = vzd.DoomGame()
# run a specific scenario
# game.set_doom_scenario_path(str(Path(vzd.scenarios_path) / "basic.wad"))
# game.set_doom_map("map01")

# render options
game.set_screen_resolution(vzd.ScreenResolution.RES_800X600)
game.set_screen_format(vzd.ScreenFormat.RGB24)
game.set_render_hud(True);              game.set_render_minimal_hud(False)  # whether hud is enabled
game.set_render_crosshair(True);        game.set_render_weapon(True)
game.set_render_decals(True);           game.set_render_particles(True)
game.set_render_effects_sprites(True);  game.set_render_messages(True)      # In-game text messages
game.set_render_corpses(True);          game.set_render_screen_flashes(True) 

# Buttons https://vizdoom.farama.org/api/python/enums/#vizdoom.Button
game.set_available_buttons([vzd.Button.MOVE_FORWARD, vzd.Button.MOVE_BACKWARD, vzd.Button.TURN_LEFT, 
                                  vzd.Button.TURN_RIGHT, vzd.Button.ATTACK, vzd.Button.USE])

# accessible data from the game
game.set_available_game_variables([vzd.GameVariable.KILLCOUNT])

# We could use the built-in window with set_window_visible(True). 
# For this example however we are going to provide the screen buffer pixels to loop_visual
game.set_window_visible(False)
# game.set_sound_enabled(True)  # sound only works if the built-in doom window were visible and in focus

game.set_mode(vzd.Mode.PLAYER)
game.init()

#store the game object in get. for global access
get.game = game
get.screen_buf = np.zeros(shape=(600,800,3), dtype=np.uint8)

class DOOM(State):        
    def on_start(self):
        get.game.new_episode()
        self.total_rewards = 0

    def loop_main(self):
        # slow down the game loop executions to a 60 fps framerate
        if millis_timer() < 16:
            return False, 0
        millis_timer.zero()
        
        if get.game.is_episode_finished():
            return True, 0
        else:
            state = get.game.get_state()
            get.screen_buf = state.screen_buffer 

            action = [False, False, False, False, False, False]

            x_mag = get.read_in('turn')
            y_mag = 1024 - get.read_in('forward') # y is inverted 1024 to 0
                      
            if y_mag < 384:
              action[0] = True
            elif y_mag > 604:
              action[1] = True
            if x_mag < 368:
              action[2] = True
            elif x_mag > 640:
              action[3] = True
            if get.read_in('shoot') == 1:
              action[4] = True
              action[5] = True

            reward = get.game.make_action(action)

            points = get.game.get_game_variable(vzd.GameVariable.KILLCOUNT)
            if points > self.total_rewards:
               self.total_rewards = points
               get.send_out('reward', 70)

        return False, 0
        
    def loop_visual(self, sketch):
        # pass the current screen_buffer to a py5 image and display it
        sketch.create_image_from_numpy(get.screen_buf, bands='RGB', dst=self.screen)
        sketch.image(self.screen, 0, 0)

    def pre_task(self, sketch):
       # we only need to create this once before the task, not at every state on_start()
       self.screen = sketch.create_image(800, 600, sketch.RGB)

#------------------------- TRAINING PROTOCOL BLOCKS AND BLOCK TRIAL STATES -------------------------

task = {
    'DOOM': DOOM(max_time_s=180, next_state='DOOM'),
}

# call the game environment's close function upon neurokraken quit
nk.load_task(task, run_at_quit=lambda: get.game.close)

nk.run()