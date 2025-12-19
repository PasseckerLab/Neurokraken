"""With a provided task/its config.py this script will open and close a timed_valve
with the set timed_valve_name for the specified number of times and durations.
This script uses serial_out entries set in your provided task's config.py
As a standalone script it allows easy calibration of the amount of liquid to be
dispensed in a given number of openings.
To run set the variables at the script begin; the timed_valve_name from your task's
config.serial_out, the total_rewards closed_time_ms, and the open_time_ms you want to use in the run.
Then run this script as python valve_test.py -t {mytaskname}
To test a control over a direct valve you can within a task run get.send_out('valve_name', True/False)
As a additional feature this script can be used as a minimal example of direct
utilization of the neurokraken networker"""

timed_valve_name = 'reward_valve'
total_rewards = 10

closed_time_ms = 400
open_time_ms = 100

import sys, argparse, importlib, importlib.util, time, py5
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--task', type=str,help ='your task folder')
parser.add_argument('-c', '--config', type=str, default='config.py', 
                    help='a file in your task that you want to use as your config.py')
args = parser.parse_args()

config_file = args.config
task = args.task

def load_module(task:str, pyfile:str):
    pyfile = pyfile if pyfile.endswith('.py') else pyfile + '.py'
    modulename = f'tasks.{task}.{pyfile[:-3]}' # i.e. i.e. tasks.examples/decision_steering.config.
    # provide the absolute module path - spec_from_file location() would otherwise search for the import 
    # relative from the variable path calling this script.
    modulepath = Path(__file__).parent.parent.parent / 'tasks' / task / pyfile
    spec = importlib.util.spec_from_file_location(modulename, modulepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[modulename] = module
    spec.loader.exec_module(module)
    return module

# insert the neurokraken root folder so that possible imports from a config can be found
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

config = load_module(task, config_file)

from neurokraken.core import networker as netw
networker = netw.Networker(serial_key='KRAKEN')

num_rewards = 0

def setup():
    global last_time, networker
    py5.size(300, 150)
    py5.window_title('Valve Test')
    py5.frame_rate(8_000)
    
    # initialize the networker communication
    networker.write_teensy_data(config.serial_out)
    last_time = time.time()
    
def draw():
    global networker, config, last_time, num_rewards
    py5.background(0)

    data_updated, _ = networker.read_teensy_data(config.serial_in)
    
    if time.time() > last_time + open_time_ms/1000 + closed_time_ms/1000 and num_rewards < total_rewards:
        config.serial_out[timed_valve_name]['value'] = int(open_time_ms)
        last_time = time.time()
        num_rewards += 1
  
    if data_updated: 
        networker.write_teensy_data(config.serial_out)

    py5.fill(255)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text_size(20)
    py5.text(f'{num_rewards} times opened', 0, 0, py5.width, py5.height)
    
    if time.time() > last_time + open_time_ms/1000 + closed_time_ms/1000 + 1.0:
        py5.exit_sketch()

py5.run_sketch()