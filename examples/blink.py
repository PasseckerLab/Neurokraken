from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in = {
}
serial_out = {'led': devices.direct_on(pin=3, start_value=False)
}

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, log_dir=None,
                 display=Display(size=(800, 600)), mode='keyboard')

#------------------------- CREATE A TASK AND RUN IT -------------------------

from neurokraken.controls import get

class Green(State):
    """We will just show the color green on a display in this state and blink an LED every 5 seconds"""
    def on_start(self):
        # store relevant variables within the state self
        self.t_last_switch = 0
        self.led_status = False

    def loop_main(self):
        if get.time_ms > self.t_last_switch + 5_000:
            self.led_status = not self.led_status
            get.send_out('led', self.led_status)
            self.t_last_switch = get.time_ms
        return False, 0
    
    def loop_visual(self, sketch):
        sketch.background(0,255,0)

task = {
    'waiting': Green(next_state='waiting'),
}

nk.load_task(task)

nk.run()