# setup configuration
from neurokraken import Neurokraken, State
from neurokraken.configurators import devices, Display, Camera, Microphone

serial_in =  {'light_beam': devices.analog_read(pin=3, keys=['s', 'w'])}
serial_out = {'reward_valve': devices.timed_on(pin=2),
              'LED': devices.direct_on(pin=4)}

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir='./', mode='keyboard')

# task design
from neurokraken.controls import get

class Poke_for_reward(State):
    def on_start(self):
        get.send_out('LED', True)

    def loop_main(self):
        if get.read_in('light_beam') < 400:
            get.send_out('reward_valve', 100)
            get.send_out('LED', False)
            get.progress_state('delay')

class Delay(State):
    pass

task = {
    'poke': Poke_for_reward(),
    'delay': Delay(next_state='poke', max_time_s=8)
}

nk.load_task(task)

nk.run()