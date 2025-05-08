# Troubleshooting guide for MATLAB Integration _for Jupyter_

This folder contains `troubleshooting.py`, a Python script that checks your environment for the dependencies required to run [MATLAB Integration for Jupyter](https://github.com/mathworks/jupyter-matlab-proxy/tree/main). The script prints the results in your terminal.


## Table of Contents
1. [Requirements](#requirements)
2. [Run Troubleshooting Script](#run-troubleshooting-script)
3. [Enable Logging](#enable-logging)
4. [Jupyter Kernelspec Installation Utility](#jupyter-kernelspec-installation-utility)

## Requirements
- Python

## Run Troubleshooting Script

Ensure the Python executable you use to run the troubleshooting script is in the same environment where you want to use the integration. 

Run the troubleshooting script:

```bash
$ curl https://raw.githubusercontent.com/mathworks/jupyter-matlab-proxy/main/troubleshooting/troubleshooting.py | python -
```

If your platform does not support `curl`, download [troubleshooting.py](https://raw.githubusercontent.com/mathworks/jupyter-matlab-proxy/main/troubleshooting/troubleshooting.py) and run it:

```bash
$ python troubleshooting.py
```

## Enable Logging

You can use logs to assist debugging when using MATLAB Integration for Jupyter. Set the environment variable `MWI_JUPYTER_LOG_LEVEL` to one of the following: `NOTSET`, `DEBUG`, `INFO`, `WARN`, `ERROR`, or `CRITICAL`. The default value is `INFO`. For more information on Python log levels, see [Logging Levels (Python)](https://docs.python.org/3/library/logging.html#logging-levels).

To set the environment variable, use the appropriate command for your environment. For example, in Linux, use the following:

```bash
# Set the logging environment variable
$ export MWI_JUPYTER_LOG_LEVEL="DEBUG"

# Start Jupyter
$ jupyter lab
```

## Jupyter Kernelspec Installation Utility

The MATLAB Integration _for Jupyter_ package in this repository includes a [kernelspec installation utility](/src/jupyter_matlab_kernel/kernelspec.py). When you install the package, the default kernelspec uses the Python executable it finds on your system PATH. However, this executable might be different from the one in the Python environment where you install the package. To correct this, the kernelspec utility modifies the kernelspec to match the correct Python executable. 

To use the kernelspec installation utility, run the following command in the terminal:

```bash
install-matlab-kernelspec
```

The kernelspec installation utility also allows you to revert changes to the original kernelspec, or to preview the changes without actually modifying the kernelspec. For more information about using the utility, use the `--help` option.

```bash
install-matlab-kernelspec --help
usage: install-matlab-kernelspec [-h] [--reset] [--preview]

Install or Reset Jupyter kernelspec for MATLAB Kernel

options:
  -h, --help  show this help message and exit
  --reset     Reset kernelspec to the default configuration
  --preview   Preview changes to kernelspec
```

----

Copyright 2023-2025 The MathWorks, Inc.

----