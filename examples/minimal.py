# setup configuration
from neurokraken import Neurokraken, State
from neurokraken.configurators import devices, Display, Camera, Microphone

serial_in = {}
serial_out = {}

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir='./', mode='keyboard')

# task design
from neurokraken.controls import get

class My_State(State):
    def loop_main(self):
        # your experiment code will loop here
        return False, 0
    
task = {
    'state_name': My_State(next_state='state_name'),
}

nk.load_task(task)

nk.run()