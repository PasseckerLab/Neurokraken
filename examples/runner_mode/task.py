# This example is the same as minimal.py but in runner mode and with a UI color control added in launch.py

from neurokraken.controls import get
from neurokraken import State

get.color = (0, 255, 0)

class Color(State):
    """We will just show the color on a display in this state and blink an LED every 5 seconds"""
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
        sketch.background(*get.color)

task = {
    'waiting': Color(next_state='waiting'),
}