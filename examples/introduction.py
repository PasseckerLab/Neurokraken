from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in  = {'my_touch_sensor': devices.binary_read(pin=30, keys=['a'])}
serial_out = {'my_reward_valve': devices.timed_on(pin=31)}

nk = Neurokraken(serial_in, serial_out, display=Display(), log_dir=None, mode='keyboard')

from neurokraken.controls import get

class Touch_When_Visible(State):
    def on_start(self):
        self.visible = False
        self.last_switch = get.time_ms

    def loop_main(self):
        if self.visible:
            if get.read_in('my_touch_sensor') == 1:
                # This sensor is currently touched, open a reward valve for 70ms, reset to not visible
                get.send_out('my_reward_valve', 70)
                self.visible=False
                self.last_switch = get.time_ms

        if get.time_ms > self.last_switch + 2000:
            # switch the visibility every 2000 milliseconds
            self.visible = not self.visible
            self.last_switch = get.time_ms

        return False, 0

    def loop_visual(self, sketch):
        sketch.background(0,0,0)    
        if self.visible:        
            sketch.fill(0, 255, 0)
            sketch.rect(200, 200, 400, 300)

task = {'my_first_state': Touch_When_Visible(next_state='my_first_state')}

nk.load_task(task)

nk.run()