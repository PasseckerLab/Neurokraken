from core.print0 import print0
import random
import pathlib, sys, subprocess
from pathlib import Path
import imageio_ffmpeg

def import_file(file_path:str, add_to_syspath=False):
    """Import a python script from a file path.
    
    This can be useful to integrate 3rd party scripts/tools into neurokraken tasks,
    that have not yet been made into proper packages.

    Args:
        file_path (str): The path to the Python file to import
        add_to_syspath (bool, optional): Whether to add the file's directory to sys.path
        which enables imports of the imported script to work.

    Returns:
        module: The imported module object
    """
    if add_to_syspath:
        sys.path.insert(0, str(Path(file_path).parent.resolve()))
    import importlib.util
    spec = importlib.util.spec_from_file_location(name='', location=file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def list_connected_recording_devices():
    """prints out which microphones and cameras are detected at which idx and what respective camera resolutions are supported.
    Does not check for GenICam type cameras"""
    import cv2, sounddevice as sd
    print('Found the following microphones:')
    for i in range(10):
        try: 
            print(f'microphone idx {i}:')
            print(f'  {sd.query_devices(i, "input")}')
        except ValueError as e:
            break
    
    print('\nfound the following connected cameras:\n')
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    cameras = subprocess.run(f'{ffmpeg_path} -list_devices true -f dshow -i dummy'.split(' '), capture_output=True, text=True)
        # "Linux": "v4l2-ctl --list-devices" for linux
    cameras = str(cameras.stderr).split('\n')
    cameras = [line for line in cameras if '(video)' in line]
    cameras = [cam.split('\"')[1].split('\"')[0] for cam in cameras]
    
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f'Camera idx \033[96m{i} - {cameras[i]}\033[0m:')
            print(f'  Default Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}')
            print(f'  FPS: {cap.get(cv2.CAP_PROP_FPS)}')
            print(f'  Brightness: {cap.get(cv2.CAP_PROP_BRIGHTNESS)}')
            print(f'  Contrast: {cap.get(cv2.CAP_PROP_CONTRAST)}')
            print(f'  Saturation: {cap.get(cv2.CAP_PROP_SATURATION)}')
            print(f'  Hue: {cap.get(cv2.CAP_PROP_HUE)}')
            print(f'  Gain: {cap.get(cv2.CAP_PROP_GAIN)}')
            print(f'  Exposure: {cap.get(cv2.CAP_PROP_EXPOSURE)}')
            print(f'  Buffer Size: {cap.get(cv2.CAP_PROP_BUFFERSIZE)}')
    
            resolutions = [(160, 120), (176, 144), (320, 240), (352, 288), (424, 240), (640, 360), (640, 480), (800, 480), (960, 540), (800, 600), (1280, 720), (1024, 768), (1280, 960), (1920, 1080), 
                           (3840, 2160)]
            print('  Testing showed the following available resolutions:')
            for width, height in resolutions:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                if cap.get(cv2.CAP_PROP_FRAME_WIDTH) == width and cap.get(cv2.CAP_PROP_FRAME_HEIGHT) == height:
                    print(f'    {width}x{height}')
            print()
            cap.release()
