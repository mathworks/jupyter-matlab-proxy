# Troubleshooting

In the environment that you have installed the package:

* Verify if the MATLAB executable is discoverable (ie. if it is in the PATH)
    ```bash
    $ which matlab
    /usr/local/bin/matlab
    ```

* Check if Python version is 3.8 or higher
    ```bash
    $ python --version
    Python 3.8.3
    ```

* Ensure that `matlab-proxy-app` and the `jupyter` executables are in the same environment as the python executable.
    For example if youare using VENV to manage your python environments:
    ```bash
    $ which python
    /home/user/my-project/packages/.venv/bin/python

    $ which matlab-proxy-app
    /home/user/my-project/packages/.venv/bin/matlab-proxy-app

    $ which jupyter
    /home/user/my-project/packages/.venv/bin/jupyter
    ```
    Notice that `matlab-proxy-app`, `jupyter` and the `python` executable are in the same parent directory, in this case it is: `/home/user/my-project/packages/.venv/bin`

* Ensure that you are launching `jupyter lab` using the same executable as listed above.

* Ensure that all three packages are installed in the same python environment
    ```bash
    # Pipe the output of pip freeze and grep for jupyter, matlab-proxy and jupyter-matlab-proxy.
    # All three packages should be highlighted in the output.
    # If you don't see anyone of them, then either the packages missing in the output have been installed
    # in a different python environment or not installed at all.
    $ pip freeze | grep -E "jupyter|matlab-proxy|jupyter-matlab-proxy"
    ```

* If the integration is not showing up as an option to the dropdown box in the Jupyter notebook:
    ```bash
    #Run the following commands and verify that you are able to see similar output:
    
    $ jupyter serverextension list
    config dir: /home/user/anaconda3/etc/jupyter
        jupyter_server_proxy  enabled
        - Validating...
        jupyter_server_proxy  OK
        jupyterlab  enabled
        - Validating...
        jupyterlab 3.5.1 OK
    
    $ jupyter nbextension list
    Known nbextensions:
    config dir: /home/user/anaconda3/etc/jupyter/nbconfig
        notebook section
        jupyter-js-widgets/extension  enabled
        - Validating: OK
        tree section
        jupyter_server_proxy/tree  enabled
        - Validating: OK  $ pip freeze | grep -E "jupyter|matlab-proxy|jupyter-matlab-proxy"
    
    $ jupyter labextension list
        jupyterlab_pygments v0.2.2 enabled OK (python, jupyterlab_pygments)
        jupyter_matlab_labextension v0.1.0 enabled OK
        @jupyterlab/server-proxy v3.2.2 enabled OK


    # IF the server does not show up in the commands above, install:
    $ pip install jupyter-contrib-nbextensions
    ```

----

Copyright (c) 2021-2023 The MathWorks, Inc. All rights reserved.

----
