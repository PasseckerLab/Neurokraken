with_cutie = False

# ------------------------ TASK SETUP ------------------------

from neurokraken import Neurokraken, State
from neurokraken.configurators import devices, Camera

serial_in = {
    'lick_left': devices.binary_read(pin=10, keys=['a']),
    'lick_right': devices.binary_read(pin=11, keys=['d'])
}

serial_out = {
    'reward_left': devices.timed_on(pin=20),
    'reward_right': devices.timed_on(pin=21)
}

cam_width, cam_height = 1280, 720
cameras = [Camera(name='camera', width=cam_width, height=cam_height)]
if not with_cutie:
    cameras = []

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, cameras=cameras,
                 log_dir='./', mode='keyboard')

#------------------------- CREATE A TASK AND RUN IT -------------------------

from neurokraken.controls import get

class Lick_left(State):
    def loop_main(self):
        if get.read_in("lick_left") == 1:
            get.log['trials'][-1]['t_lick_l'] = get.read_in('t_ms')
            get.send_out('reward_right', 60)
            return True, 0 
        return False, 0

class Lick_right(State):
    def loop_main(self):
        if get.read_in("lick_right") == 1:
            get.log['trials'][-1]['t_lick_r'] = get.read_in('t_ms')
            get.send_out('reward_left', 60)
            return True, 0 
        return False, 0

task = {
    'lick_left': Lick_left(max_time_s=60_000, next_state='lick_right'),
    'lick_right': Lick_right(max_time_s=60_000, next_state='lick_left', trial_complete=True)
}

nk.load_task(task)

if not with_cutie:
    nk.run()
    exit()

# ------------------------ CUTIE TRACKING AND UI ------------------------

# The approach is the same as in toolkit/cutie/live_webcam_example.py using the same optimizations of a 
# parallel_predict() loop/thread and pre-created numpy- and py5 images for shared usage and performance,
# but now with the added context of a neurokraken task

cutie_config_path = r'C:\path\to\cloned\repository\of\Cutie\cutie\config'
reference_folder = r'C:\Path\to\folder\of\reference\imageJPGs\and\maskPNGs\pairs\created\with\cutie\interactivedemo'

from py5 import Sketch
import threading
from pathlib import Path
import numpy as np

# import the cutie processing utilities script using import_file - this approach can be used for integrating
# python projects saved in disparate folders.
from neurokraken import tools
cutils_path = str(Path(__file__).parent.parent / 'toolkit/cutie/cutils.py')
cutils = tools.import_file(cutils_path)

cutils.create_cutie(cutie_config_path)
cutils.load_references(reference_folder)

processed_frame = np.zeros(shape=(cam_height, cam_width, 3), dtype=np.uint8)
masks =           np.zeros(shape=(cam_height, cam_width, 3), dtype=np.uint8)

def parallel_predict():
    # cutie will keep predicting frames in this loop. In a proper experiment we might also save the created masks,
    # calculate information like the center of mass, and add relevant data for the experiment to get.log
    global processed_frame, masks
    while True:
        if get.quitting:
            break
        frame = get.camera(0)
        # cutie works on RGB images => turn the frame from greyscale i.e. (720, 1280) into RGB (720, 1280, 3)
        frame = np.stack([frame, frame, frame], axis=-1)
        processed_frame, masks = cutils.predict_frame(frame, apply_pallete=True)

class UI(Sketch):
    def settings(self):
        self.size(800, 300, self.P2D)

    def setup(self):
        global processed_frame_py5, masks_py5
        processed_frame_py5 = self.create_image(1280, 720, self.RGB)
        masks_py5 =           self.create_image(1280, 720, self.RGB)

    def draw(self):
        global processed_frame, masks, processed_frame_py5, masks_py5

        self.background(50)
        
        self.create_image_from_numpy(processed_frame, bands='RGB', dst=processed_frame_py5)
        self.image(processed_frame_py5, 0, 0, 400, 300)

        self.create_image_from_numpy(masks, bands='RGB', dst=masks_py5)
        self.image(masks_py5, 400, 0, 400, 300)

    def exiting(self):
        get.quit()

threading.Thread(target=parallel_predict, daemon=True).start()

ui = UI()
ui.run_sketch(block=False)

nk.run()
