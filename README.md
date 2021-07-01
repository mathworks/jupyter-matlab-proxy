# MATLAB Integration for Jupyter

The `jupyter-matlab-proxy` Python® package allows you to integrate MATLAB® with Jupyter®. The MATLAB integration for Jupyter enables you to open a MATLAB desktop in a web browser tab, directly from your Jupyter environment. This is not a kernel integration.

The MATLAB Integration for Jupyter is under active development and you might find issues with the MATLAB graphical user interface. For support or to report issues, see the [Feedback](#Feedback) section.


## Use the MATLAB Integration for Jupyter

Once you have a Jupyter environment with the `jupyter-matlab-proxy` package installed, to use the integration, follow these steps:

1. Open your Jupyter environment.

2. If you are using Jupyter Notebook (on the left in figure below), on the `New` menu, select `MATLAB`. If you are using JupyterLab (on the right in figure below), select the MATLAB icon on the launcher.

<p align="center">
  <img width="600" src="img/combined_launchers.png">
</p>

3. If prompted to do so, enter credentials for a MathWorks account associated with a MATLAB license. If you are using a network license manager, change to the _Network License Manager_ tab and enter the license server address instead. To determine the appropriate method for your license type, consult [MATLAB Licensing Info](./MATLAB_Licensing_Info.md).

<p align="center">
  <img width="400" src="img/licensing_GUI.png">
</p>

4. Wait for the MATLAB session to start. This can take several minutes.

5. To manage the MATLAB integration for Jupyter, click the tools icon shown below.

<p align="center">
  <img width="100" src="img/tools_icon.png">
</p>

6. Clicking the tools icon opens a status panel with buttons like the ones below:

    <p align="center">
      <img width="800" src="img/status_panel.png">
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
python -m pip install https://github.com/mathworks/jupyter-matlab-proxy/archive/0.1.0.tar.gz
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

## Advanced 

### Environment Variables

To control the behavior of the MATLAB integration for Jupyter, you can optionally specify the environment variables described in this section. You must specify these variables before starting your Jupyter environment. For example, specify the variable `APP_PORT` to be equal to 8888 when you start the Jupyter notebook using the command below:

```bash
env APP_PORT=8888 jupyter notebook
```
**MARKDOWN TABLE**

These values are preset for you when you access the integration from the Jupyter console.
| Name | Type | Example Value | Description |
| ---- | ---- | ------------- | ----------- |
| **MLM_LICENSE_FILE** | string | `"1234@111.22.333.444"` | When you want to use either a license file or a network license manager to license MATLAB, specify this variable.</br> For example, specify the location of the network license manager to be `123@hostname`|                                                                         
| **LOG_LEVEL** | string | `"CRITICAL"` | Specify the Python log level to be one of the following `NOTSET`, `DEBUG`, `INFO`, `WARN`, `ERROR`, or `CRITICAL`. For more information on Python log levels, see [Logging Levels](https://docs.python.org/3/library/logging.html#logging-levels) .<br />The default value is `INFO`. |
| **LOG_FILE** | string | `"/tmp/logs.txt"` | Specify the full path to the file where you want the logs to be written. |
| **BASE_URL** | string | `"/matlab"` | Set to control the base URL of the app. BASE_URL should start with `/` or be `empty`. |
| **APP_PORT** | integer | `8080` | Specify the port for the HTTP server to listen on. |
| **CUSTOM_HTTP_HEADERS** | string  |`'{"Content-Security-Policy": "frame-ancestors *.example.com:*"}'`<br /> OR <br />`"/path/to/your/custom/http-headers.json"` |Specify valid HTTP headers as JSON data in a string format<br />OR <br /> Specify the full path to the JSON file containing (valid) HTTP headers. These headers would be injected into the HTTP response sent to the browser. </br> For  more information, see the CUSTOM_HTTP_HEADERS sub-section in the Advanced Usage section. |


## Feedback

We encourage you to try this repository with your environment and provide feedback – the technical team is monitoring this repository. If you encounter a technical issue or have an enhancement request, send an email to `jupyter-support@mathworks.com`.


## Advanced Usage

#### CUSTOM_HTTP_HEADERS: 
If the browser renders the MATLAB Integration for Jupyter with some other content, then web browsers could block the integration because of mismatch of `Content-Security-Policy` header in the response headers from the integration.

To avoid this, providing custom HTTP headers allow browsers to load the content.

For example:
If this integration is rendered along with some other content on the domain `www.example.com`, sample `http-headers.json` file could be something like:

```json
{
  "Content-Security-Policy": "frame-ancestors *.example.com:* https://www.example.com:*;"
}
```
or if you are passing the custom http headers as a string in the environment variable. In bash shell, it could look like :

```bash
export CUSTOM_HTTP_HEADERS='{"Content-Security-Policy": "frame-ancestors *.example.com:* https://www.example.com:*;"}'
```

If you add the `frame-ancestors` directive, the browser does not block the content of this integration hosted on the domain `www.example.com`


For more information about `Content-Security-Policy` header,  check Mozilla developer docs for [Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)

**NOTE**: Setting custom HTTP headers is an advanced manoeuver, only use this functionality if you are familiar with HTTP headers.