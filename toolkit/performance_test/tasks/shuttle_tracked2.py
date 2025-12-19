with_cutie = True

# ------------------------ TASK SETUP ------------------------

from neurokraken import Neurokraken, State
from neurokraken.configurators import devices, Display, Camera

serial_in = {
    't_ms': devices.time_millis(logging=True),
    'pulse_clock': devices.pulse_clock(pin=22, change_periods_ms=100),
    'lick_left': devices.binary_read(pin=28, keys=['a']),
    'lick_right': devices.binary_read(pin=29, keys=['d']),
    't_us': devices._time_micros(logging=True)
}

serial_out = {
    'reward_left': devices.timed_on(pin=0),
    'reward_right': devices.timed_on(pin=1)
}

cam_width, cam_height = 1280, 720
camera = Camera(name='Kayeton_mono_2.8-12mm', width=cam_width, height=cam_height,
                max_capture_fps=100, vid_fps=100)
if not with_cutie:
    cameras = []

from pathlib import Path
log_dir = Path(__file__).parent.parent.parent.parent / 'logs'

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir=log_dir,
                 mode='teensy', cameras=[camera],
                 log_performance=True, subject={'ID': 'performance_test_2'})

#------------------------- CREATE A TASK AND RUN IT -------------------------

from neurokraken.controls import get


class Lick_left(State):
    def loop_main(self):
        global threshold_left
        if get.time_ms > 600_000:
            get.quit()
        # as the random triggers will keep hitting both sides faster than a subject can 
        # reasonably shuttle between them add non-triggering 3 seconds at the start of each state for this test
        if get.read_in("lick_left") == 1 and get.time_ms > self.start_time + 3000:
            get.log['trials'][-1]['t_lick_l'] = get.read_in('t_ms')
            get.send_out('reward_right', 60)
            return True, 0 
        return False, 0

class Lick_right(State):
    def loop_main(self):
        if get.time_ms > 600_000:
            get.quit()
        global threshold_right
        if get.read_in("lick_right") == 1 and get.time_ms > self.start_time + 3000:
            get.log['trials'][-1]['t_lick_r'] = get.read_in('t_ms')
            get.send_out('reward_left', 60)
            return True, 0 
        return False, 0

task = {
    'lick_left': Lick_left(max_time_s=60_000, next_state='lick_right'),
    'lick_right': Lick_right(max_time_s=60_000, next_state='lick_left', trial_complete=True)
}

nk.load_task(task)

if not with_cutie and __name__ == '__main__':
    nk.run()
    exit()

# ------------------------ CUTIE TRACKING AND UI ------------------------

cutie_config_path = r'C:\Users\q131aw\Desktop\code\cutieTest\Cutie\cutie\config'
reference_folder = r'C:\Users\q131aw\Desktop\code\cutieTest\Cutie\workspace\cutieTestB\reference'

from py5 import Sketch
import threading
from pathlib import Path
import numpy as np

# import the cutie processing utilities script using import_file
from neurokraken import tools as exph
cutils_path = str(Path(__file__).parent.parent.parent.parent / 'toolkit/cutie/cutils.py')
cutils = exph.import_file(cutils_path)

cutils.create_cutie(cutie_config_path)
cutils.load_references(reference_folder)

processed_frame = np.zeros(shape=(cam_height, cam_width, 3), dtype=np.uint8)
masks =           np.zeros(shape=(cam_height, cam_width, 3), dtype=np.uint8)

def parallel_predict():
    # cutie will keep predicting frames. In a proper experiment we might also save the created masks
    # calculate information like the center of mass, and add relevant data for the experiment to get.log
    global processed_frame, masks
    while True:
        if get.quitting:
            break
        frame = get.camera(0)
        # turn the frame from greyscale i.e. (720, 1280) into RGB (720, 1280, 3) for cutie processing
        frame = np.stack([frame, frame, frame], axis=-1)
        processed_frame, masks = cutils.predict_frame(frame, apply_pallete=True)

class UI(Sketch):
    def settings(self):
        self.size(800, 300, self.P2D)

    def setup(self):
        global processed_frame_py5, masks_py5
        processed_frame_py5 = self.create_image(1280, 720, self.RGB)
        masks_py5 = self.create_image(1280, 720, self.RGB)

    def draw(self):
        global processed_frame, masks, processed_frame_py5, masks_py5

        self.background(50)
        
        self.create_image_from_numpy(processed_frame, bands='RGB', dst=processed_frame_py5)
        self.image(processed_frame_py5, 0, 0, 400, 300)

        self.create_image_from_numpy(masks, bands='RGB', dst=masks_py5)
        self.image(masks_py5, 400, 0, 400, 300)

        self.text(f'{get.time_ms} ms\n{get.time_ms // 1000}s\n{get.time_ms // 60_000}min', 410, 20)
        self.text(f'camera fps: {get.threads_info['framerate_cams']['Kayeton_mono_2.8-12mm']:.1f}\nframerate main: {get.threads_info['framerate_main']:.1f}', 410, 60)
        self.text(f'touch left: {get.read_in('lick_left')}\ntouch right: {get.read_in('lick_right')}', 470, 20)

    def exiting(self):
        get.quit()

if __name__ == '__main__':
    threading.Thread(target=parallel_predict, daemon=True).start()

    ui = UI()
    ui.run_sketch(block=False)

    nk.run()

