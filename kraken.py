import os, sys, argparse
from pathlib import Path
import importlib.util

from neurokraken.core.print0 import print0
from neurokraken.neurokraken import Neurokraken

#------------------------- TASK SELECTION -------------------------

task_path = Path(__file__, '..', 'tasks').resolve()
tasks = [folder.parts[-1] for folder in task_path.iterdir() if folder.is_dir()]
tasks = [str(t) for t in tasks]

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--task', choices=tasks, type=str, help ='your task folder')
parser.add_argument('-c', '--config', type=str, help='a file in your task that you want to use as your config.py')
parser.add_argument('-e', '--experiment', type=str, help='a file in your task that you want to use as your task.py')
parser.add_argument('-s', '--subject', type=str, help='The subject ID from a subjects.json')
parser.add_argument('-k', '--keyboard', action='store_true', help='simulate/fake a teensy and run tasks with the keyboard')
parser.add_argument('-a', '--agent', action='store_true', help='run the task with a programmatic agent')
parser.add_argument('-q', '--noquestions', action='store_true', help='skip ask_for questions')
parser.add_argument('-l', '--nolog', action='store_true', help='don\'t create/save a log for this run')
parser.add_argument('-r', '--repeat', action='store_true', help='repeat the last run setup (task/config,...)')

args = parser.parse_args()

if not Path('history/last_args.txt').exists():
    with open('history/last_args.txt', 'w') as f:
        # create an empty file to use as github doesn't track it.
        pass
if args.repeat:
    with open('history/last_args.txt', 'r') as f:
        args = f.readline()
    args = parser.parse_args(args.split(' '))
else:
    with open('history/last_args.txt', 'w') as f:
        f.write(' '.join(sys.argv[1:]))

from rich.prompt import Prompt
if args.task:
    task = args.task
else:
    task = Prompt.ask("Enter your task", choices=tasks) #, default='minimal')

task_path = task_path / task

def find_taskfile(file_name, default_name:str, task_folder):
    if not file_name:
        file_name = default_name
    file_name = file_name if file_name.endswith('.py') else file_name + '.py'
    if not Path(task_folder / file_name).exists():
        print(f'{file_name} was not found in {task_folder}, Please create a file {default_name} for your task or select one of the found .py files')
        options = [f.name[:-3] for f in task_folder.glob('*.py')]
        file_name = Prompt.ask(f'Enter your {default_name[:-3]} filename', choices=options)
        file_name = file_name if file_name[-3:] == '.py' else file_name + '.py'
    return file_name

config_file = find_taskfile(file_name=args.config, default_name='config.py', task_folder=task_path)
experiment_file = find_taskfile(file_name=args.experiment, default_name='task.py', task_folder=task_path)

def load_module(task:str, pyfile:str):
    modulename = f'tasks.{task}.{pyfile[:-3]}'
    modulepath = f'tasks/{task}/{pyfile}'
    spec = importlib.util.spec_from_file_location(modulename, modulepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[modulename] = module
    spec.loader.exec_module(module)
    return module

#------------------------- QUESTIONS -------------------------

def get_subject(subjects:dict, args) -> dict:
    subject = None
    if args.subject:
        current_subjects = {subject['ID']: idx for idx, subject in enumerate(subjects)}
        if args.subject in current_subjects:
            idx = current_subjects[args.subject]
            subject = subjects[idx]
        else:
            print0(f'{args.subject} does not exist within subjects.json. Please select of one of ' + \
                    'the following or add a new entry to subjects.json', color='yellow')
    if subject is None:
        print("Who is performing the task?")
        for i, subject in enumerate(subjects):
            print(f"{i} - {subject['ID']}")
        while True:
            option = input("Enter the number corresponding to the training subject or a substring of its ID: ")
            if option.isdigit() and int(option)<len(subjects):
                subject = subjects[int(option)]
                break
            else:
                # the first subject to contain the substring will be chosen
                for i, subject in enumerate(subjects):
                    if option in subject['ID']:
                        subject = subjects[i]
                        break
            if subject is None:
                print("Invalid choice. Please enter a valid number or a substring of a subject ID.")
            else:
                break
    return subject
            
import json
config = load_module(task, config_file)

# start with an empty default
subject = {'ID': '_'}

if not args.noquestions:
    subjects = {}
    if (task_path/'subjects.json').exists():
        with open(os.path.join(task_path, 'subjects.json')) as f:
            subjects = json.load(f)
    
    if hasattr(config, 'subjects'):
        subjects = config.subjects

    if hasattr(config, 'ask_for'):
        questions = config.ask_for
    else:
        questions = []
    
    if 'ID' in questions:
        subject = get_subject(subjects, args)

    if 'weight' in questions:
        while True:
            weight = input('What is the current weight (gram)? ')
            try:
                weight = float(weight)
                break
            except ValueError as e:
                print('Invalid weight - please enter a number')
                
        subject = {**subject, 'weight (g)': weight}

    remaining_questions = [q for q in questions if not q in ['ID', 'weight']]
    for question in remaining_questions:
        subject = {**subject, question:input(f'What is the {question}? ')}

serial_in = config.serial_in
serial_out = config.serial_out

mode = 'teensy'
if args.keyboard or (hasattr(config, 'mode') and config.mode=='keyboard'):
    mode = 'keyboard'

serial_key = 'KRAKEN'
if hasattr(config, 'serial_key'):
    serial_key = config.serial_key

display = None
if hasattr(config, 'display'):
    display = config.display

cameras = []
if hasattr(config, 'cameras'):
    cameras = config.cameras

microphones = []
if hasattr(config, 'microphones'):
    microphones = config.microphones

autostart = True
if hasattr(config, 'autostart'):
    autostart = config.autostart

networker_mode = 'archivist'
if hasattr(config, 'networker_mode'):
    networker_mode = config.networker_mode

log_dir = Path(__file__) / '..' / 'logs'
if hasattr(config,'log_dir'):
    log_dir = config.log_dir
if args.nolog:
    log_dir = None

max_framerate = 8000
if hasattr(config, 'max_framerate'):
    max_framerate = config.max_framerate

import_pre_run = None
if (task_path / 'launch.py').exists():
    import_pre_run = (task_path / 'launch.py').resolve()
else:
    print0('Your task doesn\'t contain a launch.py file. Running without gui.\n' +
            'Please press Alt+Ctrl+S to start the state machine and Alt+Ctrl+Q to quit', color='green')

neurokraken = Neurokraken(serial_in, serial_out, log_dir=log_dir, mode=mode, 
                          display=display, cameras=cameras, microphones=microphones,
                          subject=subject, serial_key=serial_key, autostart=autostart, max_framerate=max_framerate,
                          config=config, task_path=task_path, import_pre_run=import_pre_run, networker_mode=networker_mode)

experiment = load_module(task, experiment_file)

start_block = None
if hasattr(experiment, 'start_block'):
    start_block = experiment.start_block

if hasattr(experiment, 'permanent_states'):
    permanent_states = experiment.permanent_states
else:
    permanent_states = []

if hasattr(experiment, 'run_post_trial'):
    run_post_trial = experiment.run_post_trial
else:
    run_post_trial = lambda : None

if hasattr(experiment, 'run_at_start'):
    run_at_start = experiment.run_at_start
else:
    run_at_start = lambda : None

if hasattr(experiment, 'run_at_quit'):
    run_at_quit = experiment.run_at_quit
else:
    run_at_quit = lambda : None

if hasattr(experiment, 'run_at_visual_start'):
    run_at_visual_start = experiment.run_at_visual_start
else:
    run_at_visual_start = lambda sketch : None

main_as_sketch = True
if hasattr(experiment, 'main_as_sketch'):
    main_as_sketch = experiment.main_as_sketch

neurokraken.load_task(experiment.task, experiment, start_block, permanent_states,
                      run_at_start, run_at_quit, run_post_trial, run_at_visual_start,
                      main_as_sketch)

neurokraken.run()