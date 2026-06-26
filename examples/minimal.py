# setup configuration
from neurokraken import Neurokraken, State
from neurokraken.configurators import devices, Display, Camera, Microphone

serial_in = {}
serial_out = {}

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir='./', mode='keyboard')

# task design
from neurokraken import get

class My_State(State):
    def loop_main(self):
        # add your experiment code here where it will run in a loop
        pass

task = My_State()

nk.load_task(task)

nk.run()