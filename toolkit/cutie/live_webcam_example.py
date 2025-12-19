from cutils import create_cutie, load_references, predict_frame
import py5, cv2

parallel_processing = True

cutie_config_path = r'C:\path\to\cloned\repository\of\Cutie\cutie\config'
reference_folder =  r'C:\Path\to\folder\of\reference\imageJPGs\and\maskPNGs\pairs\created\with\cutie\interactivedemo'

cam_idx = 0
cam_width = 1280
cam_height = 720

create_cutie(cutie_config_path)
load_references(reference_folder)

cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  cam_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)

# ------------------- VFERSION IN SINGLE LOOP (SLOW FPS) -------------------

def setup():
    py5.size(800, 300)
    py5.frame_rate(5_000)

def draw():
    global cap

    _, frame = cap.read()

    _, masks = predict_frame(frame, apply_pallete=True)

    used_frame = py5.create_image_from_numpy(frame, bands='RGB')
    py5.background(0)
    py5.image(used_frame, 0, 0, 400, 300)

    masks = py5.create_image_from_numpy(masks, bands='RGB')
    py5.image(masks, 400, 0, 400, 300)
    py5.get_surface().set_title(str(py5.get_frame_rate()))

def exiting():
    global cap
    cap.release()

if not parallel_processing:
    py5.run_sketch()



# ------------------- VERSION WITH CUTIE IN SEPARATE LOOP (FAST FPS) -------------------

from py5 import Sketch

import threading, time
import numpy as np

# We create a frame that cutie will constantly keep predicting on (starting out as a black (zeros) image)
# and that the visual loop will keep updating with current camera frames.
ready_frame = np.zeros(shape=(cam_height, cam_width, 3), dtype=np.uint8)

def parallel_predict():
    global ready_frame, processed_frame, masks
    while True:
        processed_frame, masks = predict_frame(ready_frame, apply_pallete=True)

class Visual_loop(Sketch):
    def settings(self):
        self.size(800, 300, self.P2D)

    def setup(self):
        self.frame_rate(300)
        global processed_frame_py5, masks_py5
        processed_frame_py5 = self.create_image(cam_width, cam_height, self.RGB)
        masks_py5 = self.create_image(cam_width, cam_height, self.RGB)

    def draw(self):
        global ready_frame, processed_frame, masks, cap, processed_frame_py5, masks_py5

        _, ready_frame = cap.read()
        self.background(50)
        
        self.create_image_from_numpy(processed_frame, bands='RGB', dst=processed_frame_py5)
        self.image(processed_frame_py5, 0, 0, 400, 300)

        self.create_image_from_numpy(masks, bands='RGB', dst=masks_py5)
        self.image(masks_py5, 400, 0, 400, 300)

    def exiting(self):
        cap.release()

if parallel_processing:

    threading.Thread(target=parallel_predict, daemon=True).start()

    visual = Visual_loop()

    visual.run_sketch()




# # parallel predict with framerate printing:
# # (for a more minimal example the version above was used instead)
# def parallel_predict():
#     global ready_frame, processed_frame, masks
#     num_frames = 0
#     t_start = time.time()
#     while True:
#         processed_frame, masks = predict_frame(ready_frame, apply_pallete=True)
#         print(f'cutie fps: {num_frames / (time.time() - t_start)}')
#         num_frames += 1