from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in  = {'shoot': devices.binary_read(pin=30, keys=['space']),
              'turn': devices.analog_read(pin=31, keys=['left', 'right']),
              'forward': devices.analog_read(pin=32, keys=['up', 'down'])}

serial_out = {'reward': devices.timed_on(pin=33)}

nk = Neurokraken(serial_in, serial_out, display=Display(size=(800, 600)), mode='keyboard')

import vizdoom as vzd # pip install vizdoom --pre
from neurokraken.controls import get

import numpy as np

get.fps = 60

class DOOM(State):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.game = vzd.DoomGame()

        # run a specific scenario
        # self.game.set_doom_scenario_path(str(Path(vzd.scenarios_path) / "basic.wad"))
        # self.game.set_doom_map("map01")

        # render options
        self.game.set_screen_resolution(vzd.ScreenResolution.RES_800X600)
        self.game.set_screen_format(vzd.ScreenFormat.RGB24)
        self.game.set_render_hud(True);  self.game.set_render_minimal_hud(False)  # whether hud is enabled
        self.game.set_render_crosshair(True);   self.game.set_render_weapon(True)
        self.game.set_render_decals(True);   self.game.set_render_particles(True)
        self.game.set_render_effects_sprites(True);   self.game.set_render_messages(True)  # In-game text messages
        self.game.set_render_corpses(True);   self.game.set_render_screen_flashes(True) 

        # Buttons https://vizdoom.farama.org/api/python/enums/#vizdoom.Button
        self.game.set_available_buttons([vzd.Button.MOVE_FORWARD, vzd.Button.MOVE_BACKWARD, vzd.Button.TURN_LEFT, 
                                         vzd.Button.TURN_RIGHT, vzd.Button.ATTACK, vzd.Button.USE])

        # accessible data from the game
        self.game.set_available_game_variables([vzd.GameVariable.KILLCOUNT])

        # We could use the built-in window with set_window_visible(True). 
        # For this example however we are going to provide the screen buffer pixels to loop_visual
        self.game.set_window_visible(False)
        # self.game.set_sound_enabled(True)  # sound only works if the built-in doom window were visible and in focus

        self.game.set_mode(vzd.Mode.PLAYER)
        self.game.init()

        self.screen_buf = np.zeros(shape=(600,800,3), dtype=np.uint8)
        self.total_rewards = 0
  
    def on_start(self):
        self.game.new_episode()
        self.last_frame = get.time_ms

    def loop_main(self):
        # slow down the game loop executions to the framerate
        if get.time_ms - self.last_frame < 1000/get.fps:
            return False, 0
        self.last_frame = get.time_ms
        
        if self.game.is_episode_finished():
            return True, 0
        else:
            state = self.game.get_state()
            self.screen_buf = state.screen_buffer 

            action = [False, False, False, False, False, False]

            x_mag = get.read_in('turn')
            y_mag = get.read_in('forward')
                      
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

            reward = self.game.make_action(action)

            points = self.game.get_game_variable(vzd.GameVariable.KILLCOUNT)
            if points > self.total_rewards:
               self.total_rewards = points
               get.send_out('reward', 70)

        return False, 0
        
    def loop_visual(self, sketch):
        # pass the current screen_buffer to a py5 image and display it
        sketch.create_image_from_numpy(self.screen_buf, bands='RGB', dst=self.screen)
        sketch.image(self.screen, 0, 0)

    def on_sketch_setup(self, sketch):
       # we only need to create this once before the task, not at every state on_start()
       self.screen = sketch.create_image(800, 600, sketch.RGB)

#------------------------- TRAINING PROTOCOL BLOCKS AND BLOCK TRIAL STATES -------------------------

task = {
    'DOOM': DOOM(max_time_s=180, next_state='DOOM'),
}

# call the game environment's close function upon neurokraken quit
nk.load_task(task, run_at_quit=lambda: get.current_state.game.close)

nk.run()