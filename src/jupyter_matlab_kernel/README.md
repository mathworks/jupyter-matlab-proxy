# MATLAB Kernel for Jupyter

This page provides a technical overview of the MATLAB kernel used in the [MATLAB Integration for Jupyter](https://github.com/mathworks/jupyter-matlab-proxy). 

After installing the MATLAB Integration for Jupyter, your Jupyter environment shows different options for using MATLAB in Jupyter. Click `MATLAB Kernel` to start a Jupyter notebook.

|Jupyter Notebook| JupyterLab |
|--|--|
|<p align="center"><img width="200" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/classic-jupyter-kernel.png"></p> | <p align="center"><img width="500" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/jupyterlab_kernel_icon.png"></p> |



## Technical Overview

Start a Jupyter notebook to create a MATLAB kernel. When you run MATLAB code in a notebook for the first time, you see a licensing screen to enter your MATLAB license details. If a MATLAB process is not already running, one would be started automatically.

<p align="center"><img width="600" src="../../img/kernel-architecture-dedicated.png"></p>

### Shared MATLAB Workspace (Default Behavior)

By default, multiple notebooks share the same MATLAB workspace. MATLAB processes commands from multiple notebooks on a first-in, first-out basis. 

You can use kernel interrupts to stop MATLAB from processing a request. Remember that if cells from multiple notebooks are being run at the same time, the execution request you interrupt may not be from the notebook where you initiated the interrupt.

### Dedicated MATLAB Workspace (Optional Behavior)

You can now create a dedicated MATLAB session for your notebook by using the magic command `%%matlab new_session` in a cell. This starts a separate MATLAB process exclusively for that notebook, providing an isolated workspace that is not shared with other notebooks. 

This is useful when you need to avoid conflicts with other notebooks or require an independent execution environment.

Once created, all subsequent MATLAB code in that notebook will execute in the dedicated session. Each dedicated session operates independently with its own workspace and execution queue.


## Limitations
For limitations of the MATLAB kernel, see [Limitations](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/Limitations.md).

## Feedback

To request an enhancement or technical support, [create a GitHub issue](https://github.com/mathworks/jupyter-matlab-proxy/issues) or send an email to `jupyter-support@mathworks.com`.

----

Copyright 2023-2025 The MathWorks, Inc.

----
