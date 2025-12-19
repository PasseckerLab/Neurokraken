# sadly the rich package while very powerful for expanded print features
# is not sufficiently time performant for usage within neurokraken main loop
# functionalities according to tests with the python timeit module.
# So we are using this print0 tool.

import os

class PrintZero:
    """Print zero: An extended print function.
       print0('my text', color=...) can be used as a print() function supporting colors.
       Awailable colors are: white, bright_white, cyan, red, yellow, green, blue, magenta
       
       A call to print0 can also be provided with a priority= and a topic=. If a priority is provided, only a
       print0() call that has a priority <= the priority_threshold* will actually get printed.
       If print0.set_topic_threshold(str, int) has been set, a print0(topic:str=...) call with a 
       matching topic= will be printed if it has a priority <= the set topic threshold.

       This enables using different levels and focus topics of debug information.
       For example print0('mytext', color='red', priority=1) can be used for an important alarm.
       The priority level goes from 1=most important to 3 or above=least important.
       
       You can print0.set_priority_threshold(number) and print0.set_topic_threshold(str, number)
       to define a general priority_threshold and topic specific priority threshold."""
    
    def __init__(self):
        self.priority_threshold = 2
        self.topic_priority_thresholds = {}
        #Any call to os.system enables printing colors in the command prompt afterwards
        os.system('')
        self.styles = {'white': '\033[37m',
                       'bright_white': '\033[97m',
                       'cyan': '\033[96m',
                       'red': '\033[91m',
                       'yellow': '\033[33m',
                       'green': '\033[92m',
                       'blue': '\033[94m',
                       'magenta': '\033[95m',
                       'reset': '\033[0m'}

    def set_priority_threshold(self, threshold:int):
        """Only print0() with priority <= threshold will be printed"""
        self.priority_threshold = threshold
        return self

    def set_topic_threshold(self, topic:str, priority:int):
        """Set the priority threshold to be used with a specific topic instead of the global priority_threshold"""
        self.topic_priority_thresholds[topic] = priority
        return self

    def __call__(self, text:str, color:str='white', priority:int=0, topic:str=None):
        if (not topic in self.topic_priority_thresholds and priority <= self.priority_threshold) or \
           (topic in self.topic_priority_thresholds and priority <= self.topic_priority_thresholds[topic]):
            print(f'{self.styles[color]}{text}{self.styles["reset"]}')

print0 = PrintZero()
