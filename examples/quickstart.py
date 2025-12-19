# setup configuration
from neurokraken import Neurokraken, State
from neurokraken.configurators import devices, Display, Camera, Microphone

serial_in =  {'light_beam': devices.analog_read(pin=3, keys=['s', 'w'])}
serial_out = {'reward_valve': devices.timed_on(pin=2),
              'LED': devices.direct_on(pin=3)}

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir='./', mode='keyboard')

# task design
from neurokraken.controls import get

class Poke_for_reward(State):
    def loop_main(self):
        if get.read_in('light_beam') > 512:
            get.send_out('LED', True)
            return True, 0
        else:
            get.send_out('reward_valve', 100)
            get.send_out('LED', False)
            return False, 0

task = {
    'poke': Poke_for_reward(next_state='delay'),
    'delay': State(next_state='poke', max_time_s=10)
}

nk.load_task(task)

nk.run()