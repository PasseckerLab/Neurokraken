from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in = {'t_ms': devices.time_millis(logging=True),
             'pulse_clock': devices.pulse_clock(pin=22, change_periods_ms=100),
             'rotation': devices.rotary_encoder(pins=(33, 34)),
             't_us': devices._time_micros(logging=True)
}

serial_out = {'reward': devices.timed_on(pin=5)
}

from pathlib import Path
log_dir = Path(__file__).parent.parent.parent.parent / 'logs'

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir=log_dir,
                 display=Display(size=(300, 200)), mode='teensy',
                 log_performance=True, subject={'ID': 'performance_test_0'})

from neurokraken.controls import get
import random

class Test(State):
    def loop_main(self):
        if random.random() < 0.0001:
            get.send_out('reward', 200)
        if get.time_ms > 600_000:
            get.quit()
        return False, 0
    
    def loop_visual(self, sketch):
        sketch.background(0)
        sketch.text(f'{get.time_ms} ms\n{get.time_ms // 1000}s\n{get.time_ms // 60_000}min', 10, 20)
        sketch.text(f'rotation: {get.read_in('rotation')}', 150, 20)

task = {
    'test': Test(next_state='test'),
}

nk.load_task(task)

nk.run()

