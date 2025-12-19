from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

digital_pins = [28, 29, 30, 31, 32, 8, 9, 10, 11, 12]
servo_pins = [37, 38, 39, 40, 41]

digital_reads = {f'digital{i}': devices.binary_read(pin=digital_pins[i]) for i in range(len(digital_pins))}
servos = {f'servo{i}': devices.servo(pin=servo_pins[i]) for i in range(len(servo_pins))}

serial_in = {'t_ms': devices.time_millis(logging=True),
             'pulse_clock': devices.pulse_clock(pin=22, change_periods_ms=100),
             **digital_reads,
             't_us': devices._time_micros(logging=True)
}

serial_out = servos

from pathlib import Path
log_dir = Path(__file__).parent.parent.parent.parent / 'logs'

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir=log_dir,
                 display=Display(size=(300, 200)), mode='teensy',
                 log_performance=True, subject={'ID': 'performance_test_3'})

from neurokraken.controls import get
import random

servo_pos = [90] * 5
class Test(State):
    def loop_main(self):
        global servo_pos
        for i in range(len(servos)):
            if random.random() < 0.0005:
                servo_pos[i] = random.randint(0, 179)
                get.send_out(f'servo{i}', servo_pos[i])
        if get.time_ms > 600_000:
            get.quit()
        return False, 0
    
    def loop_visual(self, sketch):
        global servo_pos
        sketch.background(0)
        sketch.text(f'{get.time_ms} ms\n{get.time_ms // 1000}s\n{get.time_ms // 60_000}min', 10, 20)
        for i in range(len(servos)):
            sketch.text(f'servo {i}: {servo_pos[i]}', 10, 80 + i*16)
        for i in range(len(digital_reads)):
            sketch.text(f'digital {i}: {get.read_in(f'digital{i}')}', 80, 20+i*16)

task = {
    'test': Test(next_state='test'),
}

nk.load_task(task)

nk.run()

