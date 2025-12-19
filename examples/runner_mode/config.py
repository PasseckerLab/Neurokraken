# Instead of being bundled with the config.py a subjects dictionary could be loaded from a .json file or remote source
subjects = [{'ID': 'Alpha', 'sex': 'female'},
            {'ID': 'Beta',  'sex': 'female'},
            {'ID': 'Gamma', 'sex': 'male'},
            {'ID': 'Delta', 'sex': 'male'}]

# runner mode can prompt for named datapoints upon execution
ask_for = ['ID', 'weight', 'group']

from neurokraken.configurators import Display, devices
display = Display(size=(800, 600))

cameras = [ ]

serial_in = { }
serial_out = {'led': devices.direct_on(pin=3, start_value=False)}