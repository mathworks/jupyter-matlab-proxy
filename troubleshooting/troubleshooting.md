# Troubleshooting guide for MATLAB Integration _for Jupyter_
We have provided a Python script, troubleshooting.py, which runs basic environment checks to determine if the required dependencies are met or not. This script does not send the information anywhere remotely and just relays information to the terminal window.


## Table of Contents
1. [Requirements](#requirements)
2. [Running the script](#running-the-script)

## Requirements
* Python

## Running the script
One can run the latest version of the troubleshooting script using the following command:

```bash
$ curl https://raw.githubusercontent.com/mathworks/jupyter-matlab-proxy/main/troubleshooting/troubleshooting.py | python -
```

Ensure that the `python` executable used to run this script is from the same environment in which you intend to use the integration. 

Also, if you are on a platform that doesn't support `curl`, please consider downloading the [troubleshooting.py](https://raw.githubusercontent.com/mathworks/jupyter-matlab-proxy/main/troubleshooting/troubleshooting.py) and running it as:

```bash
$ python troubleshooting.py
```

Alternatively, you can manually execute the below commands in the environment where you have installed the package:

* Verify that the MATLAB executable is on the PATH
```bash
$ which matlab
/usr/local/bin/matlab
```

* Check if the Python version is 3.8 or higher
```bash
$ python --version
Python 3.8.3
```

* Ensure that `matlab-proxy-app` and the `jupyter` executables are in the same environment as the Python executable.
For example, if you are using VENV to manage your Python environments:
```bash
$ which python
/home/user/my-project/packages/.venv/bin/python

$ which matlab-proxy-app
/home/user/my-project/packages/.venv/bin/matlab-proxy-app

$ which jupyter
/home/user/my-project/packages/.venv/bin/jupyter
```
Notice that `matlab-proxy-app`, `jupyter` and the `python` executable are in the same parent directory, in this case, it is: `/home/user/my-project/packages/.venv/bin`

* Ensure that you are launching `jupyter lab` using the same executable listed above.

* Ensure that all three packages are installed in the same Python environment
```bash
# Pipe the output of pip freeze and grep for jupyter, matlab-proxy and jupyter-matlab-proxy.
# All three packages should be highlighted in the output.
# If you don't see any one of them, then either the packages missing in the output have been installed
# in a different Python environment or not installed at all.
$ pip freeze | grep -E "jupyter|matlab-proxy|jupyter-matlab-proxy"
```

* If the integration is not a visible option in the dropdown box inside the Jupyter Notebook:
```bash
#Run the following commands and verify that you are able to see similar output:

$ jupyter serverextension list
config dir: /home/user/anaconda3/etc/jupyter
jupyter_server_proxy enabled
- Validating...
jupyter_server_proxy OK
jupyterlab enabled
- Validating...
jupyterlab 3.5.1 OK

$ jupyter nbextension list
Known nbextensions:
config dir: /home/user/anaconda3/etc/jupyter/nbconfig
notebook section
jupyter-js-widgets/extension enabled
- Validating: OK
tree section
jupyter_server_proxy/tree enabled
- Validating: OK $ pip freeze | grep -E "jupyter|matlab-proxy|jupyter-matlab-proxy"

$ jupyter labextension list
jupyterlab_pygments v0.2.2 enabled OK (python, jupyterlab_pygments)
jupyter_matlab_labextension v0.1.0 enabled OK
@jupyterlab/server-proxy v3.2.2 enabled OK


# IF the server does not show up in the commands above, install:
$ pip install jupyter-contrib-nbextensions
```

----

Copyright 2023 The MathWorks, Inc.

----