import sys
from pathlib import Path

path = None
if len(sys.argv) > 1:
    path = sys.argv[1]

if path is None:
    import textwrap
    note = """
    This script creates the arduino side code/configuration ready to upload from a provided python file containing serial_in and serial_out dictionaries.
    This can be a config.py file used in task folder mode or a script that by its end contains a serial_in and serial_outdictionary i.e. from imported mode.
    The entries of serial_in/serial_out have to contain entries for "arduino_class": and for "arduino_args": so that correct arduino side classes can be assembled.
    You can drag and drop a python file or folder (with a config.py inside) into the console and enter have this script parse its serial_in/serial_out and
    create the arduino side configuration. Note that all parts of the file not wrapped in if __name__ == '__main__' will be executed."""
    note = textwrap.dedent(note[1:])
    print(note)
    path = input('> ')
    path = Path(path)

if path.is_file():
    config_file = Path(path)
elif path.is_dir():
    # if the path contains a .h file move it to the teensy folder
    for file_path in path.iterdir():
        if file_path.is_file() and file_path.suffix == '.h' and file_path.name != 'Config.h':
            # Move the file to /teensy
            destination = (Path('teensy') / file_path.name)
            destination.write_bytes(file_path.read_bytes())
            print(f"Copied {file_path.name} to /teensy")
    config_file = (path / 'config.py').resolve()
    if not config_file.exists():
        print(f'no file config.py was found in the folder {path}')
        print('please enter the filename of the local config or its path:')
        config_file = input('> ')
        config_file = Path(config_file)
        if not config_file.is_file():
            # it is not a full path but just the filename
            config_file = path / config_file

import importlib.util
spec = importlib.util.spec_from_file_location(name='', location=config_file)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

serial_in = config.serial_in
serial_out = config.serial_out

if not 't_ms' in serial_in.keys():
    serial_in = {'t_ms': {'value': 0, 'encoding': 'uint', 'byte_length': 4, 'logging': False,
                 'arduino_class': 'MillisReader'},
                 **serial_in}

if not 'start_stop' in serial_out.keys():
    serial_out = {'start_stop': {'value': 0, 'encoding': 'uint', 'byte_length': 1, 
                                 'default': 0, 'reset_after_send': True,
                                 'arduino_class': 'StartStop'},
                   **serial_out}

controls:list[tuple[str,str,any]] = [(name, params['arduino_class'], params.get('arduino_args', None)) for name, params in serial_out.items()]
sensors:list[tuple[str,str,any]] = [(name, params['arduino_class'], params.get('arduino_args', None)) for name, params in serial_in.items()]

# pair arduino devices with their files to include

devices_files = [f for f in Path('teensy').glob("*") if f.is_file()]
devices_files = [(f, str(f.name)) for f in devices_files if str(f.name).endswith('.h')
                and not str(f.name) in ['config.h', 'Config.h'] and not str(f.name).startswith('_')]

# rough file parsing for in which file a given sensor/control lives. There are likely some niche conditions that can break this
def classes_in_code(code:list[str])->list[str,bool]:
    found_classes = [] # (class_name, is_process)
    uncommented = []
    for l in code:
        start_comment = l.find('//')
        if start_comment != -1:
            l = l[:start_comment].lstrip().rstrip()
            if l != '':
                uncommented.append(l)
        else:
            uncommented.append(l)
    code = '\n'.join(uncommented)
    uncommented = ''
    idx = 0
    while True:
        start_comment = code.find('/*', idx)
        if start_comment == -1:
            # no further comment start found => append the rest
            uncommented += code[idx:]
            break
        else:
            end_comment = code.find('*/', idx)
            if end_comment == -1:
                # no end comment found => append the rest
                uncommented += code[idx:]
                break
            else:
                uncommented += code[idx:start_comment]
                idx = end_comment + 2
    code = uncommented
    idx = 0
    while True:
        start_class = code.find('class ', idx)
        if start_class != 0:
            start_class = code.find(' class ', idx)
        if start_class == -1:
            start_class = code.find('\nclass ', idx)
        if start_class == -1:
            # all classes have been found
            break
        if start_class != 0:
            start_class += 1
        end_inheritance = code.find('{', start_class)
        idx = end_inheritance + 1
        if end_inheritance == -1:
            break
        inheritence = code[start_class:end_inheritance]
        if ' Control' in inheritence or ' Sensor' in inheritence or ' Process' in inheritence:
            # it is a device class
            class_name = inheritence[6:].split(':')[0].rstrip()
            is_process = False
            if ' Process' in inheritence:
                is_process = True
            found_classes.append((class_name, is_process))
    return found_classes

device_includable:dict[str,str] = {}
device_isprocess:dict[str,bool] = {}

for d in devices_files:
    with open(d[0]) as f:
        lines = f.readlines()
        classes = classes_in_code(lines)
        for c in classes:
            device_includable[c[0]] = d[1]
            device_isprocess[c[0]] = c[1]

# assemble the lines of the Config.h to be created

config_code = ''

files = []
for device in (*controls, *sensors):
    file = device_includable[device[1]]
    if not file in files:
        files.append(file)
for f in files:
    config_code += f'#include "{f}"\n'
config_code += '\n'
config_code += 'namespace config{\n'

for device in sensors:
    args = ''
    if device[2] is not None:
        if isinstance(device[2], list) or isinstance(device[2], tuple):
            args = ', '.join([str(x) for x in device[2]])
        else:
            args = str(device[2])
    line = f'  {device[1]}* {device[0]} = new {device[1]}({args});\n'

    config_code += line
config_code += '\n'

for device in controls:
    args = ''
    if device[2] is not None:
        if isinstance(device[2], list) or isinstance(device[2], tuple):
            args = ', '.join([str(x) for x in device[2]])
        else:
            args = str(device[2])
    if not device[0] in [s[0] for s in sensors]:
        # this control was not already defined as an existing sensor
        line = f'  {device[1]}* {device[0]} = new {device[1]}({args});\n'
        config_code += line
    
config_code += '\n'

config_code += f'  Sensor* sensors[] = {{{', '.join([d[0] for d in sensors])}}};\n'
config_code += f'  Control* controls[] = {{{', '.join([d[0] for d in controls])}}};\n'
config_code += f'  Process* processes[] = {{{', '.join([d[0] for d in (*sensors, *controls) if device_isprocess[d[1]]])}}};\n'
config_code += '}\n'

with open('teensy/Config.h', 'w') as f:
    f.write(config_code)
