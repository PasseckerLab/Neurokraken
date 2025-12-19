from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

digital_pins = [28, 29, 30, 31, 32, 8, 9, 10, 11, 12]
analog_pins = [24, 25, 26, 27, 15]
servo_pins = [37, 38, 39, 40, 41]
valve_pins = [0, 1, 2, 3, 4, 5, 6, 7, 16, 17]

digital_reads = {f'digital{i}': devices.binary_read(pin=digital_pins[i]) for i in range(len(digital_pins))}
analog_reads = {f'analog{i}': devices.analog_read(pin=analog_pins[i]) for i in range(len(analog_pins))}
servos = {f'servo{i}': devices.servo(pin=servo_pins[i]) for i in range(len(servo_pins))}
valves = {f'valve{i}': devices.direct_on(pin=valve_pins[i]) for i in range(len(valve_pins))}

serial_in = {'t_ms': devices.time_millis(logging=True),
             'pulse_clock': devices.pulse_clock(pin=22, change_periods_ms=100),
             **digital_reads,
             **analog_reads,
             'rotation_0': devices.rotary_encoder(pins=(33, 34)),
             'rotation_1': devices.rotary_encoder(pins=(35, 36)),
             't_us': devices._time_micros(logging=True)
}

serial_out = {**servos,
              **valves 
}
from pathlib import Path
log_dir = Path(__file__).parent.parent.parent.parent / 'logs'

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir=log_dir,
                 display=Display(size=(200, 320)), mode='teensy',
                 log_performance=True, subject={'ID': 'performance_test_4'})

from neurokraken.controls import get
import random

servo_pos = [90] * 5
valve_state = [0] * 10

class Test(State):
    def loop_main(self):
        global servo_pos
        for i in range(len(servos)):
            if random.random() < 0.0005:
                servo_pos[i] = random.randint(0, 179)
                get.send_out(f'servo{i}', servo_pos[i])
        for i in range(len(valves)):
            if random.random() < 0.0005:
                valve_state[i] = random.randint(0, 1)
                get.send_out(f'valve{i}', valve_state[i])
        if get.time_ms > 600_000:
            get.quit()
        return False, 0
    
    def loop_visual(self, sketch):
        global servo_pos
        sketch.background(0)
        sketch.text(f'{get.time_ms} ms\n{get.time_ms // 1000}s\n{get.time_ms // 60_000}min', 10, 20)
        for i in range(len(servos)):
            sketch.text(f'servo {i}: {servo_pos[i]}', 10, 80+i*15)
        for i in range(len(valves)):
            sketch.text(f'valve {i}: {valve_state[i]}', 10, 180 + i*15)
        for i in range(len(digital_reads)):
            sketch.text(f'digital {i}: {get.read_in(f'digital{i}')}', 80, 20+i*15)
        for i in range(len(analog_reads)):
            sketch.text(f'analog {i}: {get.read_in(f'analog{i}')}', 80, 190+i*15)
        sketch.text(f'rotation 0: {get.read_in('rotation_0')}', 80, 280)
        sketch.text(f'rotation 1: {get.read_in('rotation_1')}', 80, 295)

task = {
    'test': Test(next_state='test'),
}

nk.load_task(task)

nk.run()

