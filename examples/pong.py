from neurokraken import Neurokraken, State
from neurokraken.configurators import Display, devices

serial_in = {
    'movement': devices.rotary_encoder(pins=(31, 32), keys=['up', 'down'])
}

serial_out = {
    'reward_valve':   devices.timed_on(pin=40),
}

display = Display(size=(800,600))

nk = Neurokraken(serial_in=serial_in, serial_out=serial_out, 
                 display=display, mode='keyboard')

import random
from neurokraken.controls import get
from neurokraken.tools import Millis
millis_timer = Millis()

get.score = [0, 0]
get.speed = 10

class Pong(State):
    def constrain(self, value, minimum, maximum):
        return min(max(value, minimum), maximum)

    def on_start(self):
        self.paddlepos_player = 300
        self.paddlepos_ai = 300
        self.ball_pos_x, self.ball_pos_y = [400, 300]
        self.ball_velocity_x = random.choice([-get.speed, get.speed])
        self.ball_velocity_y = random.random() - 0.5 # -0.5 to +0.5
        
        self.steering_scale = 0.25
        self.last_position = get.read_in('movement')

    def loop_main(self):
        if millis_timer() < 16:
            # run at ~60 hz => only continue if 16ms have passed
            return False, 0
        millis_timer.zero()
        # update the player paddle position
        new_position = get.read_in('movement')
        delta_player = new_position - self.last_position
        # update the current position for the next loop iteration now that you have the delta
        self.last_position = new_position
        delta_player *= self.steering_scale
        self.paddlepos_player += delta_player
        self.paddlepos_player = self.constrain(self.paddlepos_player, 50, 550)

        # The "AI" will simply follow the ball y position.
        # Values/calculations here are chosen semiarbitrarily to make the AI competitive but beatable
        delta_ai = self.ball_pos_y- self.paddlepos_ai
        delta_ai = self.constrain(delta_ai, -8, 8)
        # speed down the ai paddle a bit based on its current ball distance
        delta_ai *=  1 - ((750 - self.ball_pos_x) / 700)
        self.paddlepos_ai = self.constrain(self.paddlepos_ai + delta_ai, 50, 550)

        # find the new ball position
        ball_pos_x = self.ball_pos_x + self.ball_velocity_x
        ball_pos_y = self.ball_pos_y + self.ball_velocity_y
        if ball_pos_y < 0 or ball_pos_y > 600:
            self.ball_velocity_y *= -1

        # if the ball position overlaps with either paddle its x velocity is flipped to the center
        # and a 0.3 fraction of the paddle's y velocity is added to the ball y velocity
        if ball_pos_x > 45 and ball_pos_x < 55 and \
           ball_pos_y > self.paddlepos_player-60 and ball_pos_y < self.paddlepos_player+60:
            self.ball_velocity_x = abs(self.ball_velocity_x)
            self.ball_velocity_y += delta_player * 1.0

        if ball_pos_x > 745 and ball_pos_x < 755 and \
           ball_pos_y > self.paddlepos_ai-60 and ball_pos_y < self.paddlepos_ai+60:
            self.ball_velocity_x = -abs(self.ball_velocity_x)
            self.ball_velocity_y += delta_ai * 1.0

        self.ball_velocity_y = self.constrain(self.ball_velocity_y, -4, 4)

        # now that all values have been calculated, updated the change to self.ball_pos
        self.ball_pos_x, self.ball_pos_y = ball_pos_x, ball_pos_y

        # if a left or right edge was reached, log the win/loss, provide a reward, and finish the trial
        finished = False
        if self.ball_pos_x > 800:
            get.score[0] += 1
            get.log['trials'][-1]['win'] = True # log the outcome
            get.send_out('reward_valve', 70)
            finished = True
        if self.ball_pos_x < 0:
            get.score[1] += 1
            get.log['trials'][-1]['win'] = False
            finished = True

        return finished, 0
        
    def loop_visual(self, sketch):
        sketch.background(0)
        sketch.stroke(255);   sketch.fill(255)
        sketch.stroke_weight(10);   sketch.stroke_cap(sketch.SQUARE)

        sketch.line(400, 0, 400, 600) # center line. we could also use sketch variables like sketch.width/2
        
        sketch.line(50, self.paddlepos_player-50, 50, self.paddlepos_player+50)
        sketch.line(750, self.paddlepos_ai-50, 750, self.paddlepos_ai+50)

        sketch.circle(self.ball_pos_x, self.ball_pos_y, 20)

        sketch.text_align(sketch.CENTER, sketch.CENTER)
        sketch.text_size(60)
        sketch.text(f'{get.score[0]}        {get.score[1]}', 400, 40)

task = {
    'pong': Pong(next_state='pong', trial_complete=True),
}

nk.load_task(task)

nk.run()