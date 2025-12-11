# MATLAB Integration _for Jupyter_

[![PyPI badge](https://img.shields.io/pypi/v/jupyter-matlab-proxy.svg?logo=pypi)](https://pypi.python.org/pypi/jupyter-matlab-proxy) [![codecov](https://codecov.io/gh/mathworks/jupyter-matlab-proxy/branch/main/graph/badge.svg?token=ZW3SESKCSS)](https://codecov.io/gh/mathworks/jupyter-matlab-proxy) [![Downloads](https://static.pepy.tech/personalized-badge/jupyter-matlab-proxy?period=month&units=international_system&left_color=grey&right_color=blue&left_text=PyPI%20downloads/month)](https://pepy.tech/project/jupyter-matlab-proxy)



Run MATLAB® code in Jupyter® environments such as Jupyter notebooks, JupyterLab, and JupyterHub.


## Table of Contents
- [MATLAB Integration _for Jupyter_](#matlab-integration-for-jupyter)
  - [Table of Contents](#table-of-contents)
  - [Features of MATLAB Integration _for Jupyter_](#features-of-matlab-integration-for-jupyter)
  - [Requirements](#requirements)
  - [Install](#install)
    - [Install from PyPI](#install-from-pypi)
    - [Build from Source](#build-from-source)
    - [Using VS Code](#using-vs-code)
    - [Using JupyterHub and The Littlest JupyterHub](#using-jupyterhub-and-the-littlest-jupyterhub)
    - [Using Simulink](#using-simulink)
    - [Troubleshooting](#troubleshooting)
  - [Get Started](#get-started)
  - [Run MATLAB Code in a Jupyter Notebook](#run-matlab-code-in-a-jupyter-notebook)
    - [Notes](#notes)
  - [Open MATLAB in a Browser](#open-matlab-in-a-browser)
  - [Edit MATLAB Files in JupyterLab](#edit-matlab-files-in-jupyterlab)
  - [Limitations](#limitations)


## Features of MATLAB Integration _for Jupyter_

You can use this package to run MATLAB code in Jupyter notebooks and JupyterLab.

<p><img width="600" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/JupyterKernel.gif"></p>

From your Jupyter notebook or JupyterLab, you can also open the MATLAB development environment in your browser to access more MATLAB features.

<p><img width="600" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/JupyterMATLABDesktop.gif"></p>

## Requirements

* Supported operating systems:
  - Linux®
  - MacOS
  - Windows® (supported from [v0.6.0](https://github.com/mathworks/jupyter-matlab-proxy/releases/tag/v0.6.0)).
  - Windows Subsystem for Linux (WSL 2) [Installation Guide](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/install_guides/wsl2/README.md).

* Python versions: 3.10 | 3.11 | 3.12 | 3.13

* MATLAB R2020b or later, installed and on the system PATH.
  ```bash
  # Confirm MATLAB is on the PATH
  which matlab
  ```
  Note: You only need MATLAB installed if you want to execute MATLAB code. You can open Jupyter notebooks containing MATLAB code without having MATLAB installed.

* System dependencies required to run MATLAB:
  - The [MATLAB Dependencies](https://github.com/mathworks-ref-arch/container-images/tree/main/matlab-deps) repository contains `base-dependencies.txt` files that list the libraries required to run each release of MATLAB on a given operating system. To see how to use these files, refer to the Dockerfiles in the same folder.

* Linux based systems also require `X Virtual Frame Buffer (Xvfb)`, which you can install with:

  ```bash
  # On a Debian/Ubuntu based system:
  $ sudo apt install xvfb

  # On a RHEL based system:
  $ yum search Xvfb
  xorg-x11-server-Xvfb.x86_64 : A X Windows System virtual framebuffer X server.
  $ sudo yum install xorg-x11-server-Xvfb
  ```

## Install

Install this Python package from the Python Package Index (PyPI) or build it from the source.

### Install from PyPI

```bash
python -m pip install jupyter-matlab-proxy
install-matlab-kernelspec
```
For more information on `install-matlab-kernelspec`, see [Jupyter Kernelspec Installation Utility](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/troubleshooting/troubleshooting.md#jupyter-kernelspec-installation-utility).

Installing this package will not install MATLAB. To execute MATLAB code in Jupyter, you must have [MATLAB installed](https://www.mathworks.com/help/install/install-products.html) separately.

### Build from Source

Alternatively, you can install this package by building it from the source. This requires Node.js® version 18 or higher. To install Node.js, see [Node.js Downloads](https://nodejs.org/en/download/).
```bash
git clone https://github.com/mathworks/jupyter-matlab-proxy.git
cd jupyter-matlab-proxy
python -m pip install .
install-matlab-kernelspec
```

### Using VS Code

You can use this package to run MATLAB in Jupyter notebooks using VS Code. For instructions, see [Run MATLAB in Jupyter Notebooks Using VS Code](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/install_guides/vscode/README.md).

### Using JupyterHub and The Littlest JupyterHub

To use MATLAB with JupyterHub, install the `jupyter-matlab-proxy` Python package in the Jupyter environment launched by your JupyterHub platform. For example, if your JupyterHub platform launches Docker containers, install this package in the Docker image used to launch those containers, using the instructions for [Using MATLAB Integration _for Jupyter_ in a Docker Container](https://github.com/mathworks-ref-arch/matlab-integration-for-jupyter).

To use MATLAB with [The Littlest JupyterHub (TLJH)](https://tljh.jupyter.org/en/stable/index.html#), see [MATLAB Integration for Jupyter on The Littlest JupyterHub](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/install_guides/the-littlest-jupyterhub/README.md). You might use this if you want to set up JupyterHub on a single server for a small number of users, such as students in a class.

### Using Simulink

This package lets you use Simulink® programmatically by entering commands in a Jupyter notebook. To view a model or use other Simulink features that require the Simulink UI, you can use a VNC to connect your Jupyter environment to a Linux desktop where you have MATLAB and Simulink installed. For instructions, see [MATLAB Jupyter VNC Solution](https://github.com/mathworks/jupyter-matlab-vnc-proxy).

### Troubleshooting

To troubleshoot package installation issues, see [Troubleshooting](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/troubleshooting/troubleshooting.md).


## Get Started

This section shows you how to:

1. [Run MATLAB Code in a Jupyter Notebook](#run-matlab-code-in-a-jupyter-notebook)
2. [Open MATLAB in a Browser](#open-matlab-in-a-browser)
3. [Edit MATLAB files in JupyterLab](#edit-matlab-files-in-jupyterlab)

Install Jupyter Notebook or JupyterLab:

  ```bash
  # For Jupyter Notebook
  python -m pip install notebook

  # For JupyterLab 4
  python -m pip install jupyterlab
  ```

Note: you can use this package to execute MATLAB code in both JupyterLab 3 and 4, but syntax highlighting is only supported on JupyterLab 4.


Open your Jupyter environment by starting Jupyter Notebook or JupyterLab.

  ```bash
  # For Jupyter Notebook
  jupyter notebook

  # For JupyterLab
  jupyter lab
  ```

If you are prompted for a token, click the link shown in your terminal to access your Jupyter environment.

After installing this package, you see new MATLAB options in your Jupyter environments.


| Classic Notebook Interface | JupyterLab |
| :---: | :---: |
|<img width="200" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/classic-jupyter_icons.png">|<img width="300" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/jupyterlab_icons_1.png">|


## Run MATLAB Code in a Jupyter Notebook

To open a Jupyter notebook where you can run MATLAB code, click `MATLAB Kernel` in your notebook or JupyterLab.


| Classic Notebook Interface | JupyterLab |
| :---: | :---: |
|<img width="200" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/classic-jupyter-kernel.png"> | <img width="300" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/jupyterlab_kernel_icon.png">|

This opens a Jupyter notebook that supports MATLAB.

<p align="center"><img width="600" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/jupyterlab-notebook.png"></p>


### Notes

- **Licensing:** When you execute MATLAB code in a notebook for the first time, enter your MATLAB license information in the dialog box that appears. For details, see [Licensing](https://github.com/mathworks/matlab-proxy/blob/main/MATLAB-Licensing-Info.md). The MATLAB session can take a few minutes to start.

- **Sharing MATLAB across  notebooks:** By default, multiple notebooks running on a Jupyter server share the underlying MATLAB process, so executing code in one notebook affects the workspace in others. To use a dedicated MATLAB for your kernel instead, use the magic `%%matlab new_session`. For details, see [Magic Commands for MATLAB Kernel](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/src/jupyter_matlab_kernel/magics/README.md). To learn more about the kernel architecture, see [MATLAB Kernel for Jupyter](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/src/jupyter_matlab_kernel/README.md).

- **MATLAB Kernel:** The MATLAB kernel supports tab completion and rich outputs:
  * Inline static plot images
  * LaTeX representation for symbolic expressions
  * Tables formatted using HTML instead of ASCII, in MATLAB R2024a and later:
    | Before R2024a | After R2024a |
    |--|--|
    |<p align="center"><img width="450" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/tables_before_r2024a.png"></p> | <p align="center"><img width="400" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/tables_after_r2024a.png"></p> |

  For a technical overview of the MATLAB kernel, see [MATLAB Kernel for Jupyter](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/src/jupyter_matlab_kernel/README.md).


- **Local functions:** With MATLAB R2022b and later, you can define a local function at the end of the cell where you want to call it:
    <p><img width="350" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/local_functions.png"></p>

- **Magic Commands:** You can use predefined magic commands in a Jupyter notebook with the MATLAB kernel, and you can also implement your own. To see a list of predefined magic commands, run `%%lsmagic`. For details about using magic commands, see [Magic Commands for MATLAB Kernel](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/src/jupyter_matlab_kernel/magics/README.md).


## Open MATLAB in a Browser

To access more MATLAB features, you can open the MATLAB development environment in your browser. Click the `Open MATLAB` button in your notebook or JupyterLab.


| Classic Notebook Interface | JupyterLab |
| :---: | :---: |
|<img width="200" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/open_matlab_notebook.png"> | <img width="300" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/open_matlab_jupyterlab.png"> |

Notebooks in JupyterLab also have a `Open MATLAB` button on the toolbar:

<img width="300" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/open-matlab-button.png">

Clicking `Open MATLAB` opens the MATLAB development environment in a new browser tab.

<p align="center"><img width="600" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/jupyter_matlab_desktop.png"></p>

When you use the package for the first time, enter your MATLAB license information in the dialog box that appears. See [Licensing](https://github.com/mathworks/matlab-proxy/blob/main/MATLAB-Licensing-Info.md) for details.

For technical details about this MATLAB development environment, see [MATLAB in a Browser](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/src/jupyter_matlab_proxy/README.md).


## Edit MATLAB Files in JupyterLab

You can also edit MATLAB `.m` files in JupyterLab. Click the `MATLAB File` button.

<p align="center"><img width="300" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/matlabfile-icon.png"></p>

This opens an untitled `.m` file where you can write MATLAB code with syntax highlighting.

<p align="center"><img width="600" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/new-matlab-file.png"></p>

* Currently, this package allows you to edit MATLAB `.m` files but not to execute them.
* To open a new MATLAB `.m` file, you can also use the JupyterLab command palette. Press `CTRL+SHIFT+C`, then type `New MATLAB File` and press `Enter`.

## Limitations

* This package has limitations. For example, it does not support certain MATLAB commands. For details, see [Limitations](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/Limitations.md).

* To discuss a technical issue or submit an enhancement request, [create a GitHub issue](https://github.com/mathworks/jupyter-matlab-proxy/issues), or send an email to `jupyter-support@mathworks.com`.


----

Copyright 2021-2025 The MathWorks, Inc.

----

