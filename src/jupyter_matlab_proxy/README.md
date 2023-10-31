# Open MATLAB in a browser

This module is a part of the `jupyter-matlab-proxy` package and it enables access to MATLAB in a web browser from your Jupyter environment.

This functionality requires the following packages:
| Package | Description |
|----|----|
| [matlab-proxy](https://github.com/mathworks/matlab-proxy) | Provides infrastructure to launch MATLAB and connect to it from a web browser.|
| [jupyter-server-proxy](https://github.com/jupyterhub/jupyter-server-proxy) | Extends Jupyter environments to launch MATLAB as an external process alongside the notebook server. For more information see [GUI Launchers](https://jupyter-server-proxy.readthedocs.io/en/latest/launchers.html#jupyterlab-launcher-extension).|

To report any issues or suggestions, see the [Feedback](https://github.com/mathworks/jupyter-matlab-proxy#feedback) section.

----
## Usage

* If you are using Jupyter Notebook, select `Open MATLAB` from the `New` menu. If you are using JupyterLab, select the `Open MATLAB` icon from the JupyterLab launcher.

|Jupyter Notebook| JupyterLab |
|--|--|
|<p align="center"><img width="600" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/classic-jupyter.png"></p> | <p align="center"><img width="600" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/jupyterlab-notebook-section.png"></p> |

* To enter your license information, see [Licensing](https://github.com/mathworks/jupyter-matlab-proxy#licensing).

* Wait for the MATLAB session to start. This can take several minutes.

<p align="center">
  <img width="800" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/jupyter_matlab_desktop.png">
</p>

* To manage the MATLAB integration for Jupyter, click the tools icon shown below.

<p align="center">
  <img width="100" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/tools_icon.png">
</p>

* Clicking the tools icon opens a status panel with buttons like the ones below:

    <p align="center">
      <img width="800" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/status_panel.png">
    </p>

   The following options are available in the status panel (some options are only available in a specific context):

  | Option |  Description |
  | ---- | ---- |
  | Start MATLAB | Start your MATLAB session. Available if MATLAB is stopped.|
  | Restart MATLAB | Restart your MATLAB session. Available if MATLAB is running or starting.|
  | Stop MATLAB | Stop your MATLAB session. Use this option if you want to free up RAM and CPU resources. Available if MATLAB is running or starting.|
  | Sign Out | Sign out of MATLAB session. Use this to stop MATLAB and sign in with an alternative account. Available if using online licensing.|
  | Unset License Server Address | Unset network license manager server address. Use this to stop MATLAB and enter new licensing information. Available if using network license manager.|
  | Feedback | Provide feedback. Opens a new tab to create an issue on GitHub.|
  | Help | Open a help pop-up for a detailed description of the options.|

## Limitations
This package supports the same subset of MATLAB features and commands as MATLAB® Online, except there is no support for Simulink® Online.
[Click here for a full list of Specifications and Limitations for MATLAB Online](https://www.mathworks.com/products/matlab-online/limitations.html). 

If you need to use functionality that is not yet supported, or for versions of MATLAB earlier than R2020b, you can use the alternative [MATLAB Integration for Jupyter using VNC](https://github.com/mathworks/jupyter-matlab-vnc-proxy).

----

Copyright 2021-2023 The MathWorks, Inc.

----
