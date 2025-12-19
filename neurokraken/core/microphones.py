from py5 import Sketch
import sounddevice as sd
import soundfile as sf  
import numpy as np
import queue
from pathlib import Path
from configurators import Microphone as Microphone_config

class Microphone(Sketch):
    def __init__(self, properties:Microphone_config, run_controls, log_dict:dict, time_ms:dict, log_dir:str|Path):
        super().__init__()
        self.name = properties.name
        self.idx = properties.idx
        self.sample_rate = properties.sample_rate
        self.num_channels = properties.idx
        self.filename = properties.name
        self.run_controls = run_controls
        self.log_dir = Path(log_dir) / (self.name + '.wav')
        self.time_ms = time_ms
        self.log_dict = log_dict

        self.log_dict[self.name] = []
        self.keyframe_last = 0
        self.keyframe_interval = 10_000

        if self.sample_rate is None:
            self.sample_rate = int(sd.query_devices(self.idx, 'input')['default_framerate'])

        self.q = queue.Queue()    
        self.total_frames = 0

        self.has_started = False
        self.t_start = 0

        # this automatically opens the file for usage from now on
        self.save_file = sf.SoundFile(str(self.log_dir), mode='x', samplerate=self.sample_rate,
                                      channels=self.num_channels, subtype='PCM_24')

        self.stream = sd.InputStream(device=self.idx, samplerate=self.sample_rate, 
                                     channels=self.num_channels, callback=self.callback)

    def callback(self, indata:np.ndarray, frames, time, status):
        # indata is shape (frames, channels)
        # frame number could be set as blocksize= in sd.InputStream()
        self.total_frames += frames # +1136
        # if status:
        #     print(f'microphone issue: {status}')
        if self.has_started:
            self.q.put(indata.copy())
            if self.time_ms['value'] - self.keyframe_last > self.keyframe_interval:
                self.keyframe_last = self.time_ms['value']
                # [task time ms, audio file time]
                self.log_dict[self.name].append((self.time_ms['value'], 
                                                 f'{int((self.total_frames / self.sample_rate) // 60)}m:{(self.total_frames / self.sample_rate) % 60:.3f}s'))

    def settings(self):
        self.size(5, 5)
    
    def setup(self):
        self.get_surface().set_visible(False)
        self.frame_rate(50)

    def draw(self):
        # print(self.stream.cpu_load())
        if self.run_controls.quitting:
            self.shutdown()
            return
        if self.run_controls.active:
            if not self.has_started:
                self.has_started = True
                self.stream.start()
                self.t_start = self.time_ms['value']
            # print(f'queue length: {self.q.qsize()}')
            self.save_file.write(self.q.get())

    def shutdown(self):
        self.stream.stop()
        total_duration = self.time_ms['value'] - self.t_start
        self.save_file.close()

        audio_duration_s = self.total_frames / self.sample_rate
        divergence = audio_duration_s - (total_duration / 1000)
        print(f'divergence: {divergence:.3f}s, total duration: {total_duration/1000:.3f}s, audio duration: {audio_duration_s:.3f}s, t_start: {self.t_start}')
        self.exit_sketch()