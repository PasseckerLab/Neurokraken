This is a runner mode example. Its device configuration, task, and parallel code (here the UI) are split into separate files.

In runner_mode keywords like `subjects=` or `cameras=` that would in imported mode be provided to the neurokraken object can 
instead be provided as variables in the respective files.

To run this task copy this folder into the tasks folder and run `kraken.bat` or `kraken.py`. Some options can be provided as runner mode arguments, i.e. `kraken.bat --task runner_mode --keybard` to directly this task folder task in keyboard mode.