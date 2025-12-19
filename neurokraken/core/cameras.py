from configurators import Camera as Camera_config
from py5 import Sketch
import numpy as np
import cv2
import time
import os
from datetime import datetime
from core.print0 import print0
from multiprocessing.pool import ThreadPool
from collections import deque

cameras = []

def get_camera(i:int, preview=False):
    """Returns the last frame from camera i as a numpy array or preview py5image.
    
    When preview=True (and the camera has been configured with ui_view_enabled=True)
    the returned image is a py5_image with the provided ui_view_scale.
    
    Since accessing the numpy array for live view is computationally expensive,
    use preview=True for displaying the camera in a py5 sketch and preview=False
    for computer vision applications.
    
    Args:
        i (int): Camera index
        preview (bool, optional): If True, returns preview image; if False, returns full frame
        
    Returns:
        numpy.ndarray or py5_image: Camera frame data
    """
    global cameras
    if preview:
        return cameras[i].preview
    else:
        # return the full size frame
        return cameras[i].get_current_frame()

class Cam_Sketch(Sketch):
    """Note that when saving video, the provided file_fps will only define the fps of the
    created video file playback - frames can be taken at any interval or speed desired up
    to the camera's max framerate and the file_fps should be chosen to fit that speed."""
    def __init__(self, properties:Camera_config, run_controls, log_dict:dict, time_ms:dict, log_dir=None,
                 show_cv2_backends=False, threads_info:dict={}, verbose=3):
        super().__init__()

        self.log_list = log_dict.setdefault(f'{properties.name}', [])
        self.time_ms = time_ms
        self.run_controls=run_controls
        self.threads_info = threads_info

        self.properties = properties

        print0.set_topic_threshold('camera', verbose)

        self.capturer = properties.capturer
        self.reverse_BGR = False
        match self.capturer:
            case 'cv2':
                self.reverse_BGR = True
                self.cap = cv2.VideoCapture(properties.idx, properties.cv2_backend)
                
                if properties.width is not None and self.properties.height is not None:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, properties.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, properties.height)
                    height, width = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                else:
                    height, width = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    print0(f'No width/height provided - using {width}, {height}. Your camera may be able to support' +
                           'higher resolution if provided in the camera config', priority=2, color='blue', topic='camera')
                
                self.cap.set(cv2.CAP_PROP_FPS, properties.cv2_fps)

                if show_cv2_backends:
                    self.show_available_backends()

                print0(f'using cv2 with backend: {self.cap.getBackendName()} for {properties.name}', 
                       priority=4, color='blue', topic='camera')

            case 'iio':
                self.reverse_BGR = False
                # imageio will automatically find suitable settings and return the most current frame.
                # As a result the practical capturing involves filtering frames that are the same as the last.
                # To reduce the number of these checks and thus compute the max_capture_fps can be reduced.
                import imageio as iio
                found_wh = False
                if properties.width is not None and properties.height is not None:
                    found_wh = True
                    self.iio_cam = iio.get_reader(f'<video{properties.idx}>', 
                                                  size=(properties.width, properties.height))
                else:
                    self.iio_cam = iio.get_reader(f'<video{properties.idx}>')
                first_frame = np.array(self.iio_cam.get_data(0))
                self.iio_last = np.copy(first_frame)
                print0(f'using imageio for {properties.name}', priority=4, color='blue', topic='camera')
                if not found_wh:
                        print0(f'no width/height provided - using {first_frame.shape[0], first_frame.shape[1]}', 
                               priority=2, color='blue', topic='camera')
                height, width = first_frame.shape[0], first_frame.shape[1]

            case 'harvesters':
                from harvesters.core import Harvester # type: ignore  - for python versions newer than harvesters supports
                path_GenTL_cti = properties.harvesters_path_GenTL_cti
                # note that if the path is wrong it will fail silently and detected cameras will simply be []
                self.h = Harvester()
                self.h.add_file(path_GenTL_cti)
                self.h.update()
                if len(self.h.device_info_list) == 0:
                    print0(f'no GenICams found. Please make sure your provided path_GenTL_cti is correct', 
                           priority=1, color='red', topic='camera')
                print0(f'found the following GenICams: {self.h.device_info_list} - using GenICam at idx: {properties.idx}',
                        priority=3, color='blue', topic='camera')
                self.ia = self.h.create(properties.idx)
                self.ia.start()
                # check height and width of a retrieved frame
                self.buffer = self.ia.fetch()
                self.buffer.queue()
                height, width = self.buffer.height, self.buffer.width

        # current live frame for access during the experiment as get_cameras(i)
        self.live_frame = cv2.UMat(np.zeros(shape=(height, width), dtype=np.uint8))

        self.greyscaling = True if self.properties.color2grey else False
        self.single_channel_to_grey = False
        if self.greyscaling and self.properties.color2grey_use_single_RGB_channel is not None:
            self.single_channel_to_grey = True
            self.channel2grey = 2 - self.properties.color2grey_use_single_RGB_channel
        
        # create a py5image to store the preview image if ui_view_enabled is True
        channeldepth = self.ALPHA if self.greyscaling else self.RGB
        # use a scaled down image to reduce the computational expense
        self.preview = self.create_image(
            int(width * self.properties.ui_view_scale),
            int(height * self.properties.ui_view_scale), channeldepth)

        self.save_vid = properties.save_as_vid
        self.save_images = properties.save_as_images

        if log_dir == None:
            self.log_name = str(datetime.now()).replace(':', ';').replace(' ', '_')
            dir = os.path.dirname(os.path.abspath(__file__))
            self.log_dir = os.path.join(dir, 'logs', f'{self.log_name}')
        else:
            self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)

        #-------------------------STREAMING - EXPERIMENTAL-------------------------
        self.stream_active = False
        if properties.stream_active:
            self.stream_active = True
            self.stream_port = properties.stream_port
            self.stream_h = int(properties.height * self.properties.stream_scaling)
            self.stream_w = int(properties.width  * self.properties.stream_scaling)
            print(f'Streaming {properties.name} on 127.0.0.1:{self.stream_port}/vid_stream')
            print('This feature is experimental and not tested for performance')
            print('If the frame appears static in your browser, right click => reload image')
            from flask import Flask, Response
            self.app = Flask(__name__) 
            @self.app.route("/vid_stream")
            def vid_stream():
                return Response(self.img_to_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

            self.pending_stream = deque()
            self.launch_thread(self.run_waitress, name='waitress')

        #-------------------------SET UP IMAGE SAVING-------------------------
        if self.save_images:
            self.frame_dir = os.path.join(self.log_dir, properties.name)
            os.mkdir(self.frame_dir)
        
            self.num_image_threads = 64
            self.image_pool = ThreadPool(processes = self.num_image_threads)
            self.pending_images = deque()

        #-------------------------VIDEO SAVING-------------------------
        if self.save_vid:
            if show_cv2_backends:
                # Set fourcc to -1 to show available video writer codecs. Since this runs the 
                # VideoWriter it creates a useless video file that can immediately be deleted
                print('available video writer codecs:')
                time.sleep(0.001)
                cv2.VideoWriter('useless.mp4', -1, 120.0, (1280, 720))
                os.remove('useless.mp4')

        if self.save_vid:
            codec = self.properties.vid_codec
            file_type = self.properties.vid_container
            fourcc = cv2.VideoWriter_fourcc(*codec)
            save_path = os.path.join(self.log_dir, self.properties.name + '.' + file_type)
            self.out = cv2.VideoWriter(save_path, fourcc, self.properties.vid_fps,
                                       (width, height), isColor=not self.greyscaling)

    def settings(self):
        self.size(20, 20)

    def setup(self):
        self.get_surface().set_visible(False)
        self.frame_rate(self.properties.max_capture_fps)

        self.current_frame = 0

    def draw(self):
        if self.run_controls.quitting:
            self.shutdown()
            return

        match self.capturer:
            case 'cv2':
                ret, frame_read = self.cap.read()
                # the frame_read.shape will have 3 color channels even for greyscale cameras
            case 'iio':
                frame_read = self.iio_cam.get_next_data()
                # get_next_data() will return the most recent frame. Check whether this frame is actually new
                if np.array_equal(frame_read[:,0], self.iio_last[:,0]):
                    return
                else:
                    self.iio_last = np.copy(frame_read)
            case 'harvesters':
                self.buffer = self.ia.fetch()
                self.component = self.buffer.payload.components[0].data
                # the buffer will start to be overwritten at queue() - use a copy saved beforehand
                frame_read = np.reshape(np.copy(self.component), (self.buffer.height ,self.buffer.width))
                self.buffer.queue()
                    
        # reduce the cpu load a bit by using UMat (opencv transparent API) (use .get() to get np array)
        frame = cv2.UMat(frame_read)
        if self.greyscaling and frame_read.ndim==3:
            # don't try to convert if the frame is already single channel
            if self.single_channel_to_grey:
                frame = cv2.extractChannel(frame, self.channel2grey)
            elif self.reverse_BGR:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            # the frame is now 2-dimensional, i.e. .shape = 720, 1280
        if self.properties.turn_image:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        vid_time = self.calc_vid_time(self.current_frame)

        # keep the frame so that the experiment can access it if needed
        self.live_frame = frame

        if self.properties.ui_view_enabled:
            if self.frame_count % self.properties.ui_view_step == 0:
                preview = cv2.resize(frame, (self.preview.width, self.preview.height))
                if self.reverse_BGR:
                    preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
                self.create_image_from_numpy(preview.get(), bands='L', dst=self.preview)

        # EXPERIMENTAL
        if self.stream_active:
            if self.frame_count % self.properties.stream_step == 0:
                stream_view = cv2.resize(frame, (self.stream_w, self.stream_h)).get()
                # Stream the frame
                self.pending_stream.append(stream_view)

        self.threads_info['framerate_cams'][self.properties.name] = self.get_frame_rate()

        if not self.run_controls.active:
            return
        
        self.log_list.append((self.time_ms['value'], self.current_frame, vid_time))

        # Save the frame
        if self.save_vid and not self.save_images:
            if not self.reverse_BGR:
                # reverse RGB it for the cv2 video writer if necessary
                self.out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            else:
                self.out.write(frame)
            self.current_frame += 1
        elif self.save_images:
            while len(self.pending_images) > 0 and self.pending_images[0].ready():
                # pop any completed threads from the queue to make space for new threads
                _ = self.pending_images.popleft().get()
            if len(self.pending_images) < self.num_image_threads:
                # If there is space in the threads
                task = self.image_pool.apply_async(self.save_image, (frame, self.current_frame, vid_time))
                self.pending_images.append(task)
                self.current_frame += 1
                if self.save_vid:
                    if not self.reverse_BGR:
                        # reverse RGB it for the cv2 video writer if necessary
                        self.out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                    else:
                        self.out.write(frame) 
            else:
                print0(f'all {self.num_image_threads} image saving threads are in use', 
                       priority=1, color='red', topic='camera')

    def save_image(self, frame, frame_idx, vid_time):
        save_path = os.path.join(self.frame_dir, f'{frame_idx}_{vid_time}.png'.replace(':', ';'))
        cv2.imwrite(save_path, frame)
        
        return True

    def calc_vid_time(self, frame_idx):
        millis = frame_idx * (1./self.properties.vid_fps) * 1000
        secs = millis / 1000
        mins = secs / 60
        hours = mins / 60

        millis %= 1000
        secs %= 60
        mins %= 60
        vid_time_string = f'{int(hours)}h:{int(mins)}m:{int(secs)}s:{int(millis)}ms'
        return vid_time_string

    def get_current_frame(self):
        """returns the last frame as a np.array"""
        return self.live_frame.get()

    def img_to_stream(self):
        # start with an empty backup array
        new_frame = np.zeros((100, 100), np.uint8)
        while True:
            while len(self.pending_stream) > 0:
                new_frame = self.pending_stream.popleft()
            # Don't try to outsource this img/byte encoding to an additional apply_async, this will
            # brake the streaming down to ~11 very laggy fps. This server function is async enough 
            _, current_frame = cv2.imencode('.jpg', new_frame)
            current_frame = current_frame.tobytes()
            
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + current_frame + b'\r\n')

    def run_waitress(self):
        """this function is blocking - run it in a thread"""
        import waitress
        waitress.serve(self.app, host="0.0.0.0", port=self.stream_port)

    def show_available_backends(self):
        def get_names(identifier_number):
            return [cv2.videoio_registry.getBackendName(i) for i in identifier_number]
        print(f'available backends with webcam {self.properties.name}')
        print(f'available cv2 install backends: {get_names(cv2.videoio_registry.getBackends())}')
        print(f'available camera backends: {get_names(cv2.videoio_registry.getCameraBackends())}')
        print(f'available writer backends: {get_names(cv2.videoio_registry.getWriterBackends())}')

    def shutdown(self):
        self.no_loop()
        # provide the camera processes time to finish before ending the script
        time.sleep(0.5)
        match self.capturer:
            case 'cv2':
                self.cap.release()
            case 'iio':
                self.iio_cam.close()
            case 'harvesters':
                self.ia.stop()
                self.ia.destroy()
        if self.save_vid:
            # the camera was recording a video
            self.out.release()
        self.exit_sketch()