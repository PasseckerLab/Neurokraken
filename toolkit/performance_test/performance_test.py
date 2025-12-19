"""The windows ressource scheduling causes milliseconds range lags in the python-side main loop.
Some libraries of the python ecosystem can require heavy compute resources impacting your main loop perfromance.
This script can be used to get an idea of their impact on your system and whether it makes sense to outsource its calls to loops/threads other than the main loop, or even look for less demanding replacements.
This script also shows performance data of your cameras allowing you to finetune their target framerate/frame size.
To use this script run an experiment with an explicitly defined milliseconds and microseconds time in its serial_in that are logging=True.
serial_in = {'t_ms': devices.time_millis(logging=True), 't_us': devices._time_micros(logging=True)}
In real experiments these entries do not provide practical benefits and should be excluded to not log thousands of extra events every second"""

from pathlib import Path
import json
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--last', action='store_true', help ='use the last experiment')
args = parser.parse_args()
if args.last:
    # use the most recent log
    log_dir = Path(__file__).parent.parent.parent/'logs'
    print(log_dir)
    # print(list(log_dir.glob('*')))
    logs = [f for f in log_dir.glob('*') if f.name != '.gitkeep']
    if len(logs) == 0:
        print(f'no logs found in the logs directory')
        exit()
    log_dates = [log.stat().st_mtime for log in logs]
    log = logs[np.argmax(log_dates)]
    log = log
else:
    print('please drag your log folder into the console and press enter')
    log = input('> ')
    log = Path(log)

log = log / 'log.json'
print(f'opening: {log}')

with open(str(log)) as file:
    log = json.load(file)

main_loop_t = log['t_main_loop']
main_loop_diff = np.diff(main_loop_t)
main_loop_mean = np.mean(main_loop_diff)
main_loop_stddev = np.std(main_loop_diff)
main_loop_fps = len(main_loop_t) / main_loop_t[-1] * 1000
main_loop_max = max(main_loop_diff)

received_t = log['t_received']
received_diff = np.diff(received_t)
received_mean = np.mean(received_diff)
received_stddev = np.std(received_diff)
received_fps = len(received_t) / received_t[-1] * 1000
received_max = max(received_diff)

t_ms = log['t_ms'] # set logging to True
t_ms = [t[1] for t in t_ms]
t_ms_diff = np.diff(t_ms)
t_ms_mean = np.mean(t_ms_diff)
t_ms_stddev = np.std(t_ms_diff)
t_ms_vps = len(t_ms) / t_ms[-1] * 1000
t_ms_max = np.max(np.abs(t_ms_diff - t_ms_mean))

t_us = log['t_us']
t_us = [t[1] for t in t_us]
t_us_diff = np.diff(t_us) - 1000 # 1ms has passed between samplings
t_us_mean = np.mean(t_us_diff)
t_us_stddev = np.std(t_us_diff)
t_us_vps = len(t_us) / t_us[-1] * 1000000
t_us_max = np.max(np.abs(t_us_diff - t_us_mean))

import matplotlib as mpl
from matplotlib import pyplot as plt
import numpy as np

plt.style.use('dark_background')
fig = plt.figure(figsize=(6, 6))
fig.canvas.manager.window.showMaximized()
plt.tight_layout() 
gs = mpl.gridspec.GridSpec(4, 1, height_ratios=[1,1,1,1], width_ratios=[1], hspace=0.4) # 2 rows, 1 cols
ax0 = plt.subplot(gs[0]) # gs[0,0]
plt.plot(main_loop_t[:-1], main_loop_diff)
plt.ylabel('np.diff main loop')
plt.title(f'Main Loop: #frames: {len(main_loop_t)}, framerate: {main_loop_fps:.2f}it/s, diff mean: {main_loop_mean:.2f}ms, diff stddev: {main_loop_stddev:.2f}ms, diff max: {main_loop_max:.2f}ms')
plt.subplot(gs[1])
plt.title(f'Communications: #loops: {len(received_t)}, framerate: {received_fps:.2f}it/s, diff mean: {received_mean:.2f}ms, diff stddev: {received_stddev:.2f}ms, diff max: {received_max:.2f}ms')
plt.ylabel('np.diff communications')
plt.plot(received_t[:-1], received_diff)
plt.subplot(gs[2])
plt.title(f'sensor sampling (using ms sensor): #values: {len(t_ms)}, vals/s: {t_ms_vps:.2f}, diff mean: {t_ms_mean:.2f}ms, diff stddev: {t_ms_stddev:.2f}ms, diff max: {t_ms_max:.2f}ms')
plt.ylabel('np.diff t_ms')
plt.plot(t_ms[:-1], np.diff(t_ms))
plt.subplot(gs[3])
plt.ylabel('np.diff t_us -1000')
plt.title(f'us precision (using us sensor): #values: {len(t_us)}, vals/s: {t_us_vps:.2f}, diff mean: {t_us_mean:.2f}us, diff stddev: {t_us_stddev:.2f}us, diff max: {t_us_max:.2f}us')
plt.plot(t_us[:-1], t_us_diff)

plt.show()