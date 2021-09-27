# MATLAB Integration for Jupyter
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/mathworks/jupyter-matlab-proxy/MATLAB%20Jupyter%20Integration?logo=github)](https://github.com/mathworks/jupyter-matlab-proxy/actions)
[![PyPI badge](https://img.shields.io/pypi/v/jupyter-matlab-proxy.svg?logo=pypi)](https://pypi.python.org/pypi/jupyter-matlab-proxy)
[![codecov](https://codecov.io/gh/mathworks/jupyter-matlab-proxy/branch/main/graph/badge.svg?token=ZW3SESKCSS)](https://codecov.io/gh/mathworks/jupyter-matlab-proxy)
***

The `jupyter-matlab-proxy` Python® package allows you to integrate MATLAB® with Jupyter®. The MATLAB integration for Jupyter enables you to open a MATLAB desktop in a web browser tab, directly from your Jupyter environment. This is not a kernel integration.

The MATLAB Integration for Jupyter is under active development and you might find issues with the MATLAB graphical user interface. For support or to report issues, see the [Feedback](https://github.com/mathworks/jupyter-matlab-proxy#feedback) section.


## Use the MATLAB Integration for Jupyter

Once you have a Jupyter environment with the `jupyter-matlab-proxy` package installed, to use the integration, follow these steps:

1. Open your Jupyter environment.

2. If you are using Jupyter Notebook (on the left in figure below), on the `New` menu, select `MATLAB`. If you are using JupyterLab (on the right in figure below), select the MATLAB icon on the launcher.

<p align="center">
  <img width="600" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/combined_launchers.png">
</p>

3. If prompted to do so, enter credentials for a MathWorks account associated with a MATLAB license. If you are using a network license manager, change to the _Network License Manager_ tab and enter the license server address instead. To determine the appropriate method for your license type, consult [MATLAB Licensing Info](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/MATLAB-Licensing-Info.md).

<p align="center">
  <img width="400" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/licensing_GUI.png">
</p>

4. Wait for the MATLAB session to start. This can take several minutes.

5. To manage the MATLAB integration for Jupyter, click the tools icon shown below.

<p align="center">
  <img width="100" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/tools_icon.png">
</p>

6. Clicking the tools icon opens a status panel with buttons like the ones below:

    <p align="center">
      <img width="800" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/status_panel.png">
    </p>

   The following options are available in the status panel (some options are only available in a specific context):

   * Start MATLAB Session — Start your MATLAB session. Available if MATLAB is stopped.
   * Restart MATLAB Session — Restart your MATLAB session. Available if MATLAB is running or starting.
   * Stop MATLAB Session — Stop your MATLAB session. Use this option if you want to free up RAM and CPU resources. Available if MATLAB is running or starting.
   * Sign Out — Sign out of MATLAB. Use this to stop MATLAB and sign in with an alternative account. Available if using online licensing.
   * Unset License Server Address — Unset network license manager server address. Use this to stop MATLAB and enter new licensing information. Available if using network license manager.
   * Feedback — Send feedback about the MATLAB Integration for Jupyter. This action opens your default email application.
   * Help — Open a help pop-up for a detailed description of the options.


## Installation

The `jupyter-matlab-proxy` package requires a Linux® operating system.

If you want to install this package in a Jupyter Docker® image, see [Use MATLAB Integration for Jupyter in a Docker Container](https://github.com/mathworks-ref-arch/matlab-integration-for-jupyter/tree/main/matlab). Otherwise, if you want to install the `jupyter-matlab-proxy` package into a preexisting Jupyter environment, follow the instructions below.

To install the `jupyter-matlab-proxy` package, follow these steps in your Jupyter environment on a Linux OS:

1. Install a MATLAB 64 bit Linux version. Make sure the the installation folder is on the system path. This integration supports MATLAB R2020b or later. For earlier versions, use the alternative [MATLAB Integration for Jupyter using VNC](https://github.com/mathworks/jupyter-matlab-vnc-proxy).
2. Install software packages that MATLAB depends on and software packages that this integration depends on. For a list of required software packages in a Debian based distribution, inspect [this Dockerfile](https://github.com/mathworks-ref-arch/matlab-integration-for-jupyter/blob/main/matlab/Dockerfile).
3. Install [Node and Node Package Manager](https://nodejs.org/en/) version 13 or higher.
4. Install the `jupyter-matlab-proxy` package by executing:
```bash
python -m pip install jupyter-matlab-proxy
```

If you want to use this integration with JupyterLab®, ensure that you have JupyterLab installed on your machine by running the following command:
```bash
python -m pip install jupyterlab
```

You should then install `jupyterlab-server-proxy` JupyterLab extension. To install the extension, use the following command:

``` bash
jupyter labextension install @jupyterlab/server-proxy
```

For more information see [GUI Launchers](https://jupyter-server-proxy.readthedocs.io/en/latest/launchers.html#jupyterlab-launcher-extension).


### Limitations

This package supports the same subset of MATLAB features and commands as MATLAB Online. For a full list supported products and limitations, see [Specifications and Limitations](https://www.mathworks.com/products/matlab-online/limitations.html). For a list of browser requirements, see [Cloud Solutions Browser Requirements](https://www.mathworks.com/support/requirements/browser-requirements.html). If you need to use functionality that is not yet supported, you can leverage the alternative [MATLAB Integration for Jupyter using VNC](https://github.com/mathworks/jupyter-matlab-vnc-proxy).

### Integration with JupyterHub

If you want to use this integration with JupyterHub®, then you must install the `jupyter-matlab-proxy` Python package in the Jupyter environment launched by your JupyterHub platform. For example, if your JupyterHub platform launches Docker containers, then install this package in the Docker image used to launch them. You can find a reference architecture that installs the `jupyter-matlab-proxy` Python package in a Docker image in the repository [Use MATLAB Integration for Jupyter in a Docker Container](https://github.com/mathworks-ref-arch/matlab-integration-for-jupyter/tree/main/matlab).

## Feedback

We encourage you to try this repository with your environment and provide feedback – the technical team is monitoring this repository. If you encounter a technical issue or have an enhancement request, send an email to `jupyter-support@mathworks.com`.