# utilities for automated cutie tracking

- cutils.py contains functions that can be used/imported for adding cutie functionalities into other projects and are described below
- Cutie can be found at https://github.com/hkchengrex/Cutie and can be used as a powerful tracking tool.
- process_folder.py uses reference image/mask pairs created with cutie's `interactive_demo.py` to continue tracking the objects in a provided folder of frames
- live_webcam_example.py also uses a folder of reference image/mask pairs but exemplifies using `cutils.predict_frame()` to create a live tracking on numpy arrays/images received from a camera. 

## live_webcam example

This example in `live_webcam_example.py` contains 2 version depending on how you set the variable `parallel_processing = False` at the beginning of the script.
- The first version without parallel processing uses a single py5 draw loop() to retrieve the frame of the connected camera, show it in the left half of the window, use it to predict masks with cutie, and show the mask on the right half of the window.
- The second version with `parallel_processing = True` shows the same in its py5 sketch, but has cutie predictions running in a minimal `while True:` loop parallel to the sketch that captures camera frames and displays visuals.
  - Compared to the first approach, outsourcing the cutie processing to its own thread in our example raises the cutie processing from 5fps to 15fps
  - (to target even higher framerates you can try a different image size, cutie configuartion and GPU)
  - A similar AI loop/thread is a reccommended pattern for AI processing tasks within neurokraken to not slow down the main loop of your task
  - An empty frame (np.zeros) is created before the thread is started. This frame is accessed as a global variable from both the py5 sketch that updates the variable with the current camera frame, and the cutie loop which continuously creates masks for the current frame.
  - Further shared global variables exists for the masks frame created by cutie and the corresponding unmodified processed frame
  - creating py5images is very compute intensive, so as another optimization we create them once during setup and update them with create_image_from_numpy and dst=

# cutils.py

## create_cutie(cutie_config_path:str, config_name='gui_config')

Run this function first to create a cutie instance for usage. You need to have cloned the cutie repository and point cutie_config_path to your `'C:\path\to\cloned\repository\of\Cutie\cutie\config'`. By default this function will use gui_config.yaml unless you note a different file. Changing the entries of the .yaml file allows changing cuties long term/short term focus, and its speed/scale/compute requirements.

## load_references(reference_folder:str|Path):

Run this function before predict_folder or predict_frame to load reference images and their corresponding masks that cutie should keep tracking from a specified folder. Cuties interactive_demo.py allows easy creation of image/mask pairs which can then be gathered as jpg/png file pairs from the Cutie/workspace folder corresponding to your used video.

## predict_folder(image_folder:str, mask_output_folder:str, first_file_idx:int=0):

## predict_frame(frame:np.ndarray, apply_pallete=False) -> tuple[np.ndarray, np.ndarray]: