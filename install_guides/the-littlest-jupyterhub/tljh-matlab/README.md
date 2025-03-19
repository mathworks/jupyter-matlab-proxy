# MATLAB Plugin for The Littlest JupyterHub

This guide shows you now to use the MATLAB Plugin to install [MATLAB on The Littlest JupyterHub](https://github.com/mathworks/jupyter-matlab-proxy/jupyter-matlab-proxy/install_guides/the-littlest-jupyterhub/README.md).

## Background

The Littlest JupyterHub supports [plugins](https://tljh.jupyter.org/en/latest/contributing/plugins.html) that provide additional features. The MATLAB plugin for TLJH installs:

* a specified version of MATLAB, as well as any MATLAB toolboxes
* the system libraries that MATLAB requires 
* the [MATLAB Integration for Jupyter](github.com/mathworks/jupyter-matlab-proxy), for running MATLAB in Jupyter notebooks and accessing the MATLAB environment from Jupyter.

## Using the Plugin
To install the MATLAB plugin for TLJH, include `--plugin tljh-matlab` in the Installer Script.

For example, the following command sets up an `admin_user` with `admin_password` and installs `tljh-matlab`:
```bash
curl -L https://tljh.jupyter.org/bootstrap.py
  | sudo python3 - \
    --admin admin_user:admin_password \
    --plugin tljh-matlab
```

For more information on customizing the TLJH installer, see [Customizing the Installer (TLJH)](https://tljh.jupyter.org/en/latest/topic/customizing-installer.html).


## Customizing MATLAB Installation
To customize the default values used by the plugin to install MATLAB, set the relevant environment variables before using the bootstrap command:

| Environment Variable Name | Default Values | Notes |
|---|---|---|
| MATLAB_RELEASE             | R2024b                         | Specify the MATLAB release you would like to install. |
| MATLAB_PRODUCT_LIST        | "MATLAB Symbolic_Math_Toolbox" | Specify a product by consulting the `--products` section of [MATLAB Package Manager](https://github.com/mathworks-ref-arch/matlab-dockerfile/blob/main/MPM.md). For example, to install Simulink in addition to MATLAB, use `"MATLAB Simulink"`. |
| MATLAB_INSTALL_DESTINATION | /opt/matlab/R2024b             | Specify the path to the location where you want to install MATLAB. |


For example, to customize the plugin to install MATLAB R2024b and Simulink, run:
```bash
curl https://tljh.jupyter.org/bootstrap.py
  | env MATLAB_RELEASE=R2024b MATLAB_PRODUCT_LIST="MATLAB Simulink" \
    sudo python3 - \
    --admin admin_user:admin_password \
    --plugin tljh-matlab
```

----

Copyright 2024 The MathWorks, Inc.

----