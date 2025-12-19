
from typing import Callable
from core.state_machine import State_Machine as _State_Machine
import numpy as np
import py5

class Get:
    def __init__(self, serial_in:dict, serial_out:dict, config, state_machine, log:dict,
                 cameras:list, camera, threads_info:dict, log_dir:str, mode:str='teensy'):
        self.serial_in:dict = serial_in
        """Raw serial_in dictionary of dict entries - This data will be read from the teensy at every communication.
        example content:
        {'wheel_position': {'value': 0, 'encoding': int, 'byte_length': 4, 'logging': True}, ...}"""
        self.serial_out:dict = serial_out
        """Raw serial_out dictionary of dict entries - This data will be send to the teensy at every communication.
        example content:
        {'reward_valve': {'value': 0, 'encoding': 'uint', 'byte_length': 2, 'default': 0, 'reset_after_send': True}, ...}"""
        self.config = config
        """Runner-Mode only, access to all variables within config.py"""
        self.experiment = None
        """Runner-Mode only - Access to all variables within task.py"""
        self._state_machine:_State_Machine = state_machine
        """The internal state_machine object"""
        self.log:dict = log
        """The log contains 
        log['experiment_data']:dict which includes date and subject information,
        log['trials']:list which allows accessing trials - i.e. the current/most recent trial is log['trials'][-1],
        log['blocks']:list and log['states']:list which function the same way as ['trials'] to keep track of block and state transitions
        log['events']:list A general purpose list available for flexible usage
        log['serial_in]:dict Current and historical readings of all sensors
        log['controls']:dict Current and historical values of all send_out/serial_out changes enacted
        log['cameras (t_ms/#frame/vid_time)'] camera frame timing
        log['microphones (t_ms/audio_time)'] microphone frame timing
        """
        self.camera:Callable[[int, bool], np.ndarray|py5.Py5Image] = camera
        """
        Returns the last frame from camera i as a numpy array or preview py5image.
    
        When preview=True (and the camera has been configured with ui_view_enabled=True)
        the returned image is a py5_image with the provided ui_view_scale.
        
        Since accessing the numpy array for live view is computationally expensive,
        use preview=True for displaying the camera in a py5 sketch and preview=False
        for computer vision applications.
        
        Args:
            i (int): Camera index
            preview (bool, optional): If True, returns preview image; if False, returns full frame
            
        Returns:
            camera_frame: numpy.ndarray or py5_image: Camera frame data
        """
        self.cameras:list = cameras
        """A list of all camera objects in the system. Neurokraken-internal classes generally not useful within experiments"""
        self.threads_info:dict = threads_info
        """A dictionary containing 'framerate_main', 'framerate_visual' and 'framerate_cams'
        
        Useful for development and maximizing a camera's viable fps.
        framerate_cams is a dict[str:float] with individual cameras accessible by their configured name"""
        self.log_dir:str = log_dir
        """The log Path - can be used to save additional files"""
        self.mode:str = mode
        """The mode in which the task is run, one of 'teensy', 'keyboard' or 'agent'. Usage allows 
        changing task behavior depending on how the task is run"""
        self.permanent_states:list[Callable] = []
        """Permanent states provided to your task"""

        #------------------------- STATES MACHINE CALLS -------------------------
        self.blocks:dict = self._state_machine.blocks
        """Your task states.

        You can dynamically access states and modify their variables through get.block, i.e. 
        `get.blocks['my_block']['my_state'].variable = 5`

        In the common case that you provided a non-nested dictionary of task states to neurokraken.load_task()
        this dict will contain a single default block (fittingly named get.blocks['block']) containing your dictionary of states."""
        self.start:Callable = self._state_machine.start_state_machine
        """Begin your task. Only needs to be called if your config is set to autostart=False.
        A manually timed start can be useful in cases where extended preparation and the highest
        accuracy of the first few seconds is required.
        Components outside of the actual state loops and automatic logging are already executing before get.start() 
        allowing you to monitor camera feeds and sensor values before starting the actual task. 
        
        Starting resets the clock so it is discouraged to get.start() after already having ended an 
        experiment with get.stop() as new log entries would be added at a reset timescale starting from 0"""
        self.stop:Callable = self._state_machine.stop_state_machine
        "manual non-program-quitting experiment end"
        self.quit:Callable = self._state_machine.quit
        "stop the state machine, save the log and exit the program"
        # alternatives to get.current_block = 'x' and get.current_state = 'x' manual overrides
        self.switch_block:Callable[[str], None] = self._state_machine.switch_block
        """switch to a different block/state flow of your task by its name.
        Useful for manual override of the general task or its varations.

        Synonymous with get.current_block = 'x' 

        Args:
            name (str): name of the block to switch to

        Example:
            >>> from neurokraken import State
            >>> class State_A(State):
            >>>     ...
            >>> class State_B(State):
            >>>     ...
            >>> class State_C(State):
            >>>     ...
            >>> task = {
            >>> 'consistent_block' :  {'single_state': State_A(next_state='single_state')},
            >>> 'alternating_block':  {'B': State_B(next_state='C')}
            >>>                       {'C': State_C(next_state='B')}
            >>> }
            >>> nk.load_task(task)
            >>> ...
            >>> # Switch within a UI-triggered element of code
            >>> get.switch_block('alternating_block')
        """
        self.progress_state:Callable[[str], None]= self._state_machine.progress_state
        """Override the task flow to progress to a different state of this block now
        Synonymous with get.current_state = 'x'
        
        Args:
            next_state_name (str): The name of the next state to progress to
        """

    #------------------------- SERIAL -------------------------
    time_ms:int = property(fget=lambda self : self.serial_in['t_ms']['value'])
    """The current experiment time in milliseconds"""

    def read_in(self, name:str):
        """Read a value from the serial input
        
        Args:
            name (str): The name of the entry provided in serial_in
        
        returns:
            value (int): The current sensor reading

        Example:
            >>> # for the Neurokraken() initialization
            >>> from neurokraken.configurators import devices
            >>> serial_in = {'beam_break': devices.analog_read(pin=5)}
            >>> 
            >>> # in your task specific code
            >>> if get.read_in('beam_break') < 400:
        """
        return self.serial_in[name]['value']
    
    def send_out(self, name:str, value):
        """Send a value to the named device to change its state
        
        Args:
            name (str): The name of the serial_out device to be controlled
            value (int): The new state of the device. The meaning of this value depends on the device, i.e.
            a timed_on would turn on for this many seconds, while a direct_on will turn to and stay at 0 or 1 respectively.
        
        Example:

            >>> # for the Neurokraken() initialization
            >>> from neurokraken.configurators import devices
            >>> serial_out = {'reward_valve': devices.timed_on(pin=5)}
            >>> 
            >>> # in your task specific code
            >>> get.send_out('reward_valve', 70)
        """
        self.serial_out[name]['value'] = value

    #------------------------- STATES AND BLOCKS PROPERTIES -------------------------
    # the state_machine class will overwrite many of its variables like current_block throughout
    # a task, outdating references created at program start => property() allows get.current_block
    # to access and update the current value used by the state_machine.
    current_block:str = property(fget=lambda self : self._state_machine.current_block,
                                 fset=lambda self, new_block : self._state_machine.switch_block(new_block))
    """Property to get and set the current block in your task.

    This property provides convenient access to the current block of the state machine,
    allowing both reading and modification of the current block state depending on task conditions or manual intervention.
    Setting a block can alternatively be performed with get.switch_block(block_name)

    Example:

        >>> def loop_main(self):
        >>>     ...
        >>>     if num_rewards > 200 and get.current_block == 'easy_difficulty_block':
        >>>         get.current_block = 'medium_difficulty_block'
    """
    # trial_states:list = property(fget=lambda self : self._state_machine.trial_states)
    current_state = property(fget=lambda self : self._state_machine.current_state,
                             fset=lambda self, next_state : self._state_machine.progress_state(next_state))
    """Property to check and override the current state outside of the existing state_flow.

    Progressing to a new state can alternatively performed with get.progress_state(state_name)

    Example:

        >>> def key_pressed(e):
        >>>     if e.get_key() == 'm':
        >>>         print(f'old state was {get.current_state}. Override moving to "reward_state"')
        >>>         get.current_state = 'reward_state'

    #### Note on state's `on_start()` and `run_at_start=` functions
        During a state's `def on_start()` or a state's provided `run_at_start=` get.current_state still points
        to the previous state rather than the one currently starting up. This is so that parallel code like loop_visual 
        does not try to already run a state that may be reliant on a variable set up during on_start() and that the
        `current_state` accessed by elements of your task will always have its `def on_start()` and `run_at_start=` executed
        before becoming available as the `get.current.state`. If you require access to the state during these 2 startup functions,
        utilize the respective self/first argument; def on_start(self): and `def my_at_start_function(state):
    """
    # starting_state = property(fget=lambda self : self._state_machine.starting_state)
    # "starting_state is relevant only as a direct replacement for current_state during run_at_start= functions"

    current_block_trials_count:int = property(fget=lambda self : self._state_machine.current_block_trials)
    """The numebr of trials completed within the current block. 
    
    To access the number of total trials so far you can access your log: `len(get.log['trials])`
    """
   
    quitting:bool = property(fget=lambda self : self._state_machine.run_controls.quitting)
    "check whether a shutdown has been triggered - useful for shutting down self-developed parallel code"
    active:bool = property(fget=lambda self : self._state_machine.run_controls.active)
    """active can be read by elements like cameras or your code to fit their activity with the active experiment time.

    If you configure Neurokraken with autostart=False, active will be False until get.start() and be inactive again after get.stop()
    """      

# create a noninitialized Get that will be overwritten but allows for IDE typging suggestions/docstrings
get = Get.__new__(Get)
"""get. collects commonly needed experiment from the codebase. You can use them in your experiment.py or states.py
or alternatively import them from their original location in metrics.py, cameras.py,...
.get can also be used to store and access your own variables between experiment.py, ui.py, and files.
Since python function calls have a performance cost, it can be beneficial, when a function result like get.time_ms()
is needed a lot within a sequence, to store it in a local variable over repeated calls."""