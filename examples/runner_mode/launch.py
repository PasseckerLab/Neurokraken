# code that would be executed just before neurokraken.run() can be included in an optional launch.py
# This typically covers UIs and parallel analysis/processing loops like cutie

from py5 import Sketch
import py5gui as gui
from neurokraken.controls import get
import random

def recolor_background():
    get.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

class UI(Sketch):
    def settings(self):
        self.size(200, 150)

    def setup(self):
        gui.use_sketch(self)

        gui.Button(label='randomize background', pos=(25, 50), on_click=recolor_background)

    def draw(self):
        self.background(0)
        self.fill(255);     self.stroke(255);     self.text_size(15)
        self.text(f't_ms: {int(get.time_ms)}', 25, 25)
        if get.quitting:
            self.exit_sketch()

    def exiting(self):
        # end the experiment when the UI window is closed
        get.quit()

# run the UI

ui = UI()
ui.run_sketch(block=False)