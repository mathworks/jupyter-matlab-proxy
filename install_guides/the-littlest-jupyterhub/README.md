# MATLAB Integration for Jupyter on The Littlest JupyterHub

This guide shows how to set up MATLAB and the [MATLAB Integration for Jupyter](https://github.com/mathworks/jupyter-matlab-proxy) on the [The Littlest JupyterHub (TLJH)](https://tljh.jupyter.org/en/stable/index.html#). You might use this if you want to set up JupyterHub on a single server for a small number of users, such as students in a class.


## Set up TLJH

The [TLJH Documentation](https://tljh.jupyter.org/en/stable/install/index.html) contains instructions for installing TLJH in different environments. 

Once you have a working TLJH stack, you can add MATLAB into your TLJH stack using the MATLAB Plugin for The Littlest JupyterHub.

## Add MATLAB to TLJH Installation
This repository contains `tljh-matlab`, the [MATLAB Plugin for The Littlest JupyterHub](https://github.com/mathworks/jupyter-matlab-proxy/jupyter-matlab-proxy/install_guides/the-littlest-jupyterhub/tljh-matlab/README.md). 

Use the plugin to install MATLAB, its dependencies, and the MATLAB integration for Jupyter in TLJH. 

To install the MATLAB plugin, run the `bootstrap` script from your TLJH installation process again, and add the `tljh-matlab` plugin:

```bash
curl -L https://tljh.jupyter.org/bootstrap.py \
 | sudo python3 - \
   --plugin tljh-matlab
```

For more information on installing plugins into a TLJH environment, see [Customizing the Installer *(TLJH Docs)*](https://tljh.jupyter.org/en/latest/topic/customizing-installer.html#customizing-the-installer).

To customize the MATLAB plugin, for example to choose which MATLAB toolboxes to install, see [MATLAB Plugin for The Littlest JupyterHub](https://github.com/mathworks/jupyter-matlab-proxy/tree/main/install_guides/the-littlest-jupyterhub/tljh-matlab/README.md).

## Setting Up TLJH with MATLAB in Docker: Quick Demo

Execute the [start-container-with-tljh-matlab.sh](./start-container-with-tljh-matlab.sh) script to efficiently set up a sample TLJH environment with MATLAB & The MATLAB Integration for Jupyter installed within a Docker container.

```bash
./start-container-with-tljh-matlab.sh
```

Once initialized, your JupyterHub server will be accessible for notebook hosting at **http://Your-FQDN:12000**. You can view it in your browser via **http://localhost:12000/**.

To tailor the MATLAB release or to install different MATLAB toolboxes within the TLJH instance, adjust the environment variables in the [.matlab_env](./.matlab_env) file accordingly.

## Learn More

- [The Littlest JupyterHub Official Documentation (TLJH)](https://tljh.jupyter.org/en/stable/index.html).
- [When to Use the Littlest JupyterHub (TLJH)](https://tljh.jupyter.org/en/stable/topic/whentouse.html).
- [Plugins (TLJH)](https://tljh.jupyter.org/en/stable/contributing/plugins.html).


----

Copyright 2024 The MathWorks, Inc.

----

