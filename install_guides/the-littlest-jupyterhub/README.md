# MATLAB Integration for Jupyter on The Littlest JupyterHub

This guide shows how to set up MATLAB and the [MATLAB Integration for Jupyter](https://github.com/mathworks/jupyter-matlab-proxy) on the [The Littlest JupyterHub (TLJH)](https://tljh.jupyter.org/en/stable/index.html). You might use TLJH if you want to set up JupyterHub on a single server for a small number of users, such as students in a class.


## Set up TLJH

The [TLJH Documentation](https://tljh.jupyter.org/en/stable/install/index.html) contains instructions for installing TLJH in different environments. Set up a working TLJH stack.

## Add MATLAB to TLJH Installation

Add MATLAB to your TLJH installation by using the MATLAB Plugin for The Littlest JupyterHub. To install the MATLAB plugin, run the `bootstrap` script from your TLJH installation process again, and include `-- plugin tljh-matlab` plugin:

```bash
curl -L https://tljh.jupyter.org/bootstrap.py \
 | sudo python3 - \
   --plugin tljh-matlab
```

For detailed instructions on using and customizing the plugin, such as the version and toolboxes of MATLAB it installs, see the [MATLAB Plugin for The Littlest JupyterHub](https://github.com/mathworks/jupyter-matlab-proxy/tree/main/install_guides/the-littlest-jupyterhub/tljh-matlab/README.md).

## Example: Setting Up TLJH with MATLAB in Docker

Run the [start-container-with-tljh-matlab.sh](./start-container-with-tljh-matlab.sh) script to quickly set up a TLJH environment with MATLAB and the MATLAB Integration for Jupyter installed within a Docker container.

```bash
./start-container-with-tljh-matlab.sh
```

Your JupyterHub server will be accessible for hosting Jupyter Notebooks at `http://Your-FQDN:12000`. You can view it in your browser at `http://localhost:12000/`.

![JupyterHub Login Page](https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/tljh.png)

Access JupyterHub using the default credentials: the username is `admin` and the password is `password`.
You can update these default values either in the [start-container-with-tljh-matlab.sh](./start-container-with-tljh-matlab.sh) script, or from the Jupyter Admin interface.

To install a different release of MATLAB or to install different MATLAB toolboxes within the TLJH instance, modify the environment variables in the [.matlab_env](./.matlab_env) file accordingly and run `start-container-with-tljh-matlab.sh` again.

## Learn More

- [The Littlest JupyterHub Official Documentation (TLJH)](https://tljh.jupyter.org/en/stable/index.html)
- [When to Use the Littlest JupyterHub (TLJH)](https://tljh.jupyter.org/en/stable/topic/whentouse.html)
- [Plugins (TLJH)](https://tljh.jupyter.org/en/stable/contributing/plugins.html)


----

Copyright 2024 The MathWorks, Inc.

----

