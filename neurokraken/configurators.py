from dataclasses import dataclass
import types

@dataclass
class Display:
    """
    Settings for the application window.

    Attributes:
        size (tuple[int, int]): The width and height of the window in pixels.
            Defaults to (800, 600).
        position (tuple[int, int]): The position of the window.
            The position is relative to the top left corner of your primary display and follows the
            organization of your displays in the Windows Display Settings.
            You can use positions in one of your additional displays or even have task visuals
            span multiple displays (when using a sufficient size).
            Defaults to (0, 0).
        borderless (bool):  Whether the window should be displayed without borders.
            To run your task without a taskbar, i.e. as a fullscreen visual set borderless to True.
            Defaults to False.
        renderer (str): The rendering backend to use. P2D can be more performant when using many
            drawing functions. P3D enables drawing 3D environments.
            Options: 'JAVA2D', 'P2D' and 'P3D'.
            Defaults to 'JAVA2D'.
    """
    size:tuple[int,int] = (800, 600)
    position:tuple[int, int] = (0, 0)
    borderless:bool = False
    renderer:str = 'JAVA2D'
    
import cv2
@ dataclass
class Camera: 
    """
    Configuration for camera settings and video capture parameters.

    Run neurokraken.tools.list_connected_recording_devices() to list connected cameras and their indices.
    (Be aware that GenICam cameras won't be detected by this function)

    This configuration defines all configurable parameters for camera initialization,
    video capture, image processing, and output formatting.


    Attributes:
        name (str): Camera device name or identifier. Defaults to '_'.
        idx (int): Camera device index. Your first connected camera is 0, your 2nd is 1,... Defaults to 0
        capturer (str): Video capture backend to use. Defaults to 'cv2'. Alternatively 'GenICam'.
        width (int): Capture width in pixels. Defaults to None.
        height (int): Capture height in pixels. Defaults to None.
        vid_fps (int): Maximum frames per second for capture. Defaults to 500.
        cv2_backend: OpenCV capture backend constant. Defaults to cv2.CAP_DSHOW.
        max_capture_fps (int): Maximum capture frames per second. Defaults to 5000.

        turn_image (bool): Whether to turn images 180 degree. Can have slight performance impact. Defaults to False.
        grey_scaling (bool): Whether to convert to grayscale. Defaults to False.
        single_channel_to_grey (bool): Whether to extract single channel as grey. Defaults to False.
        single_channel_to_grey_channel (int): Channel index for single channel extraction. Defaults to 0.

        ui_view_active (bool): Whether to display live view in UI. Defaults to False.
        ui_view_scale (float): Resolution caling factor for UI view display. Defaults to 0.5.
        ui_view_step (int): Frame skip interval for UI view. Defaults to 1.

        save_as_vid (bool): Whether to save output as video file. Defaults to True.
        vid_codec (str): Video codec for saving. Defaults to 'mp4v'.
        vid_container (str): Video container format. Defaults to 'mp4'.
        vid_fps (int): Video frames per second for saved files. Defaults to None.
        save_as_images (bool): Whether to save frames as individual images. Defaults to False.

        stream_active (bool): Whether to enable streaming. Defaults to False.
        stream_port (int): Network port for streaming. Defaults to 50000.
        stream_scaling (float): Resolution scaling factor for streamed frames. Defaults to 0.5.
        stream_step (int): Frame skip interval for streaming. Defaults to 10.
    """
    name:str = '_'

    # capture settings
    idx:int = 0
    capturer:str = 'cv2'
    width:int = None
    height:int = None
    cv2_backend:any = cv2.CAP_DSHOW
    cv2_fps:int = 500
    harvesters_path_GenTL_cti:str = None
    max_capture_fps:int = 5_000

    # image processing
    turn_image:bool = False
    color2grey:bool = True
    color2grey_use_single_RGB_channel:int|None = None

    # sending frames to the ui
    ui_view_enabled:bool = False
    ui_view_scale:float = 0.5
    ui_view_step:int = 1

    # recording
    save_as_vid:bool = True
    vid_codec:str = 'mp4v'
    vid_container:str = 'mp4'
    vid_fps:int = 30
    save_as_images:bool = False

    # streaming
    stream_active:bool = False
    stream_port:int = 50_000
    stream_scaling:float = 0.5
    stream_step:int = 10

@ dataclass
class Microphone:
    """
    Configuration for a connected microphone.
    Run neurokraken.tools.list_connected_recording_devices() to list all connected devices and their indices

    Attributes:
        name(str): Microphone name or identifier. The .wav file and log entries will be saved under this name. Defaults to '_'.
        idx(int): Microphone device index. Your first microphone is 0, the 2nd, 1, etc. Defaults to 0.
        sample_rate(int|None: the sample rate to be used, i.e. 44100. At None the microphones default sample rate will be used. Defaults to None.
        num_channels(int): The number of channels to be recorded (Mono/Stereo). Defaults to 1.

    Example:
        from neurokraken.configurators import Microphone
        mic = Microphone(name='mic', idx=1, sample_rate=44100, num_channels=1)
        nk = Neurokraken(..., microphone_configs=[mic])
    """
    name:str = '_'

    # capture settings
    idx:int = 0
    capturer:str = 'sounddevice'
    sample_rate:int = None
    num_channels:int = 1

#------------------------- DEVICES -------------------------

@dataclass 
class _Devices:
    """These devices can be added to serial_in or serial_out of your task configuration."""

    # Sensors

    def binary_read(self, pin:int, logging=True,
                    keys:list=('F14',), keys_control=lambda keys : 1 if keys[0] else 0):
        """A digital read of a pin (HIGH or Low), (True or False). Many devices can provide a suitable
        input to an arduino pin from simple buttons to integrated touch sensors. Provides 0 or 1
        upon get.read_in(<device name>).

        Args:
            logging:bool - log changes in value for future usage. Defaults to True.

        Example:
            >>> serial_in = {'licking_sensor': true_false_sensor(pin=3)}
            >>> print(get.read_in('licking_sensor')) # 0 or 1
        """
        return {'value': 0, 'encoding': 'uint', 'byte_length': 1, 'logging': logging,
                'arduino_class': 'DigitalSensor', 'arduino_args': pin,
                'keys': keys, 'keys_control': keys_control}

    def analog_read(self, pin:int, logging=True,
                    keys:list=('F13', 'F14'), 
                    keys_control=lambda keys : 256 if keys[0] else 768 if keys[1] else 512):
        """Analog read of a pin. Provides a continuous value 0 to 1023 upon get.read_in(<device name>).
        Analog reads can be used with devices like an angle measuring potentiometer or light sensitive photoresistor.
        
        Args:
            logging:bool - log changes in value for future usage. Defaults to True.
        
        Example:
            >>> serial_in = {'rotation_potentiometer': continuous_sensor(pin=3)}
            >>> print(get.read_in('rotation_potentiometer')) # 387
        """
        return {'value': 0, 'encoding': 'uint', 'byte_length': 2, 'logging': logging,
                'arduino_class': 'AnalogSensor', 'arduino_args': pin,
                'keys': keys, 'keys_control': keys_control}
    
    def rotary_encoder(self, pins:tuple[int,int], logging=True, controls=False,
                       keys=['F13', 'F14'], 
                       keys_control=lambda keys, value : value - 0.3 if keys[0] else value + 0.3 if keys[1] else value):
        """Rotation position of rotary encoder. Returns -2,147,483,648 to +2,147,483,647 upon 
        get.read_in(<device name>).
        Rotary encoders are useful for high precision low friction rotation readings like on a
        steering wheel or treading wheel/disc.
        
        Args:
            logging:bool - log changes in value for future usage. Defaults to True.
            controls:bool - return the optional control entry for serial_out instead of the sensor_value for
                            serial_in. When adding the control running get.send_out(<device_name>) allows
                            resetting the wheel position to 0. Defaults to False
        Example:
        >>> serial_in = {'wheel_pos': rotary_encoder(pins=[3,4])}
        >>> serial_out = {'wheel_pos': rotary_encoder(pins=[3,4], controls=True)} # optional
        >>> print(get.read_in('wheel_pos')) # -5738
        >>> get.send_out('wheel_pos', True) # reset the wheel position to 0 (only if control provided to serial_out)
        """
        if not controls:
            return {'value': 0, 'encoding': int, 'byte_length': 4, 'logging': logging,
                    'arduino_class': 'RotEnc', 'arduino_args': pins,
                    'keys': keys, 'keys_control': keys_control}
        else:
            return {'value': False, 'encoding': bool, 'byte_length': 1,
                    'default': False, 'reset_after_send': True,
                    'arduino_class': 'RotEnc', 'arduino_args': pins}
                                            
    def capacitive_touch(self, pins:list[int, int], logging=True,
                         keys=['F13'], keys_control=lambda keys : 40000 if keys[0] else 200):
        """Capacitance Sensing of a connected object. Provides a 0 to 4,294,967,295. upon get.read_in(<device name>).
        The range depends on the resistors used with the connection. See documentation for example wiring.

        Capacitance sensing can be used as an easy way to detect touch or even proximity.
        
        Args:
            logging:bool - log changes in value for future usage. Defaults to True.
        
        Example:
            >>> serial_in = {'touch': capacitive_touch(pins=[3,4])}
            >>> print(get.read_in('touch')) # 481
        """
        return {'value': 0, 'encoding': int, 'byte_length': 4, 'logging': logging,
                'arduino_class': 'CapacitiveRead', 'arduino_args': pins,
                'keys': keys, 'keys_control': keys_control}
    
    def pulse_clock(self, pin:int, change_periods_ms:int, logging=True):
        """A periodically changing HIGH/LOW clock signal will be provided at the selected pin.
        This is useful to align events with external devices like neural recording hardware that may not
        have access to the context of the task executing python but can log changes in connected digital signals.
        I.e. a pulse_clock might be created to switch its HIGH/LOW state every 1000 milliseconds and its output
        pin connected to a recording device. To match the external device events at behavior time 500 seconds,
        we now just have to look at the time of its 500th digital signal change. 

        Multiple pulse clocks at different frequencies can run in parallel for redundancy,
        i.e. 4 clocks switching HIGH/LOW every 100ms, 1s, 10s, 5 minutes respectively.

        The pulse clock is a special device that is integrated with the start_stop control and will only be
        counting time when the neurokraken is started/active and until it is stopped/inactive.
        At inactive state all pins will be HIGH. Upon get.start() pulse clock pins start at 0.
        
        Args:
            change_period:int - period in milliseconds for the pulse clock to switch HIGH/LOW
            logging:bool - log changes in value for future usage. Defaults to True.

        Example:
        >>> serial_in = {'clock_100ms': pulse_clock(2,     100),
        >>>              'clock_1s':    pulse_clock(3,    1000),
        >>>              'clock_10s':   pulse_clock(4,  10_000),
        >>>              'clock_10min': pulse_clock(5, 300_000)}
        >>> ...
        >>> print(get.read_in('clock_1s')) # 1 => This pin is currently HIGH 1 and not LOW 0"""
        return {'value': 0, 'encoding': 'uint', 'byte_length': 1, 'logging': logging,
                'arduino_class': 'PulseClock', 'arduino_args': [pin, change_periods_ms]}

    def time_millis(self, logging=False):
        """A sensor for the current milliseconds.
        This sensor is required by neurokraken with the key "t_ms" as the alignment time and thus auto-added
        to serial_in as serial_in['t_ms'] if no serial_in['t_ms'] entry already exists in your serial_in.
        While you generally do not need to manually add a time_millis() you can provide an entry named "t_ms"
        to your serial_in to override the autogeneration. 
        Manually adding time_millis(logging=True) can be useful as logging every noted change of the 
        current millisecond cam confirm neurokraken sensors being captured at millisecond precision 
        when using computer or arduino setups with a heavy compute load.
        
        Args:
            logging:bool - log changes in value for future usage. Defaults to True.

        Example:
            >>> serial_in = {'t_ms': _time_millis(logging=True)}
            >>> print(get.read_in('t_ms')) # 61_673"""
        return {'value': 0, 'encoding': 'uint', 'byte_length': 4, 'logging': logging,
                'arduino_class': 'MillisReader'}
    
    def _time_micros(self, logging=False):
        """The current time in microsends. This sensor is generally not useful as the networker
        is sampling every 1 millisecond but can be used to performance test the precise time of value sampling.

        Args:
            logging:bool - log changes in value for future usage. Defaults to True.

        Example:
            >>> serial_in = {'t_us: _time_micros()}
            >>> print(get.read_in('t_us')) # 61_673_226"""
        return {'value': 0, 'encoding': 'uint', 'byte_length': 4, 'logging': logging,
                'arduino_class': 'MicrosReader'}
    
    # Controls
    
    def direct_on(self, pin:int, start_value=False):
        """Directly turn a pin HIGH (i=1) or LOW (i=0) upon get.send_out(<device_name>, i)
        This can be used to control valves, buzzers, LEDs, ... anything you can
        control with a electric logic signal. These devices can also be time-limited
        activated with the timed_on device as an alternative.
        
        Args:
           pin (int): the teensy pin wired to the controlled device
           start_value (bool): The initial value of the pin. Defaults to False (LOW).

        Example:
            >>> serial_out = {'odor_valve': direct_on_off(pin=3)}
            >>> get.send_out('odor_valve', 0) # turn the signal off / shut down the valve/LED/buzzer/...
        """
        return {'value': start_value, 'encoding': bool, 'byte_length': 1,
                'default': start_value, 'reset_after_send': False,
                'arduino_class': 'DirectOn', 'arduino_args': pin}
    
    def timed_on(self, pin:int):
        """Similar to direct_on_off for the same devices, but only turns the digital signal HIGH
        for the provided milliseconds upon get.send_out(<device_name>, <milliseconds>) before
        turning the signal LOW again. This can be used to easily provide well timed stimulus 
        lengths and reward sizes. The providable millisecond range is 0 to 65536.
        
        Args:
           pin (int): the teensy pin wired to the controlled device

        Example:
            >>> serial_out = {'reward_valve': timed_on(pin=3)}
            >>> get.send_out('reward_valve', 60) # open the valve for 60 milliseconds
        """
        return {'value': 0, 'encoding': 'uint', 'byte_length': 2,
                'default': 0, 'reset_after_send': True,
                'arduino_class': 'TimedOn', 'arduino_args': pin}
    
    def tone(self, pin:int):
        """Set the tone frequency to be output by a passive buzzer or piezo device.
        This device uses the arduino tone function. Send 0 to not provide a tone.
        The maximum providable frequency is 65_535.

        Args:
           pin (int): the teensy pin connected to the buzzer
        
        Example:
            >>> serial_out = {'frequency': tone(pin=3)}
            >>> get.send_out('frequency', 500)
        """
        return {'value': 0, 'encoding': 'uint', 'byte_length': 2,
                'default': 0, 'reset_after_send': False,
                'arduino_class': 'Tone', 'arduino_args': pin}
    
    def servo(self, pin:int):
        """A servo motor to dynamically move experiment elements upon get.send_out(<device_name>, angle)
        The angle value can range from 0 to 255.
        This device can also be used to control the strength of an LED.

        Args:
           pin (int): the teensy pin connected to the servo's control wire. Has to be a supportive pin from 0-15, 18-19, 22-25, 28-29, 33, 36-37 

        Example
            >>> serial_out = {'servo': servo(3)}
            >>> ...
            >>> get.send_out('servo', 100)
        """
        return {'value': 127, 'encoding': 'uint', 'byte_length': 1,
                'default': 127, 'reset_after_send': False,
                'arduino_class': 'ServoMotor', 'arduino_args': pin}
    
    def start_stop(self):
        """This is a special device managed by neurokraken and will be autoadded to serial_out by neurokraken if
        no serial_out['start_stop'] is found. It typically does not need to be added to a task.
        As this device is managed by neurokraken, use get.start() and get.stop() to start and stop
        to control an experiment duration in autostart=False mode instead of modifying this device data.
        
        A special control for starting and stopping the task's experiment time.
        This control is required by neurokraken to control the teensy time with the key serial_out["start_stop"]
        and thus auto-added to serial_out if no entry ["start_stop"] is fonud to already exist.
        """
        return {'value': 0, 'encoding': 'uint', 'byte_length': 1, 
                'default': 0, 'reset_after_send': True,
                'arduino_class': 'StartStop'}
    
devices = _Devices()

