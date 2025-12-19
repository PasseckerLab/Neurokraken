import serial
import serial.tools.list_ports
import keyboard
import numpy as np
from matplotlib import pyplot as plt
import csv
import argparse

plot = False

def plot_data():
    global millis, micros
    us = np.array(micros)
    us -= (us[0])
    us = us[1:-1]
    us_diff = np.diff(us) - 100_000 # a 100ms pulse clock will have each value 100_000us after the previous 
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    ax_0 = ax.twinx()
    # secondary x axis showing the logged us
    ax_0.plot(range(len(us)), us, c='magenta')
    ax_0.ticklabel_format(useOffset=False, style='plain')
    ax_0.set_ylabel('time [us]', c='magenta')

    ax.set_ylabel('np.diff() of time point minus 100ms [us]')
    ax.set_xlabel('pulse change')
    ax.plot(range(len(us_diff)), us_diff)
    ax.ticklabel_format(useOffset=False, style='plain')
    
    us_mean = np.mean(us_diff)
    us_stddev = np.std(us_diff)
    us_vps = len(us) / us[-1] * 1_000_000
    us_max = np.max(np.abs(us_diff - us_mean))

    plt.title(f'interpulse data: #values: {len(us)}, vals/s: {us_vps:.2f}, diff mean: {us_mean:.2f}us, diff stddev: {us_stddev:.2f}us, diff max: {us_max:.2f}us')
    plt.show()

def save_data():
    global millis, micros
    with open('pulse_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['millis', 'micros'])
        for ms, us in zip(millis, micros):
            writer.writerow([int(ms), int(us)])

def load_data(filename='pulse_data.csv'):
    global millis, micros
    millis, micros = [], []
    with open(filename) as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            millis.append(int(row[0]))
            micros.append(int(row[1]))

def read_key(event):
    global plot
    if keyboard.is_pressed('ctrl') and keyboard.is_pressed('alt'):
        if event.name == 'p':
            plot = True
            # using default matplotlib outside of the main thread will fail

keyboard.on_release(read_key)

millis = []
micros = []

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--load', action='store_true', help ='load local data.csv')
args = parser.parse_args()

if args.load:
    load_data()
    plot_data()
else:
    devices = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(devices):
        if 'PULSETEST' in hwid:
            com = port
    print('detected pulse change times:')
    print('time [ms]', 'time [us]')

    try:
        ser = serial.Serial(com, baudrate=115_200, timeout=0.4, write_timeout=None)
    except NameError as e:
        print(f'no connected usb device identifying as PULSETEST found')
        exit()
    while True:
        if ser.in_waiting != 0:
            ms = ser.read(4)
            ms = int.from_bytes(ms, 'little', signed=False)
            us = ser.read(4)
            us = int.from_bytes(us, 'little', signed=False)
            millis.append(ms)
            micros.append(us)
            print(ms, us)
        if plot:
            ser.close()
            save_data()
            plot_data()
            break


