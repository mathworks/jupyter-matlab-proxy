# Advanced Usage

This page lists some of the advanced manuevers that may be of specific interest to help  configure the package for use in your environment.

## Environment Variables

To control the behavior of the MATLAB integration for Jupyter, you can optionally specify the environment variables described in this section. You must specify these variables before starting your Jupyter environment. For example, a network license server can be specified when you start the Jupyter notebook using the command below:

```bash
env MLM_LICENSE_FILE="1234@example.com" jupyter notebook
```

The following table describes all the environment variables that you can set to customize the behavior of this integration.

| Name | Type | Example Value | Description |
| ---- | ---- | ------------- | ----------- |
| **MLM_LICENSE_FILE** | string | `"1234@111.22.333.444"` | When you want to use either a license file or a network license manager to license MATLAB, specify this variable.</br> For example, specify the location of the network license manager to be `123@hostname`.|                                                                         
| **MWI_BASE_URL** | string | `"/matlab"` | Set to control the base URL of the app. MWI_BASE_URL should start with `/` or be `empty`. |
| **MWI_APP_PORT** | integer | `8080` | Specify the port for the HTTP server to listen on. |
| **MWI_LOG_LEVEL** | string | `"CRITICAL"` | Specify the Python log level to be one of the following `NOTSET`, `DEBUG`, `INFO`, `WARN`, `ERROR`, or `CRITICAL`. For more information on Python log levels, see [Logging Levels](https://docs.python.org/3/library/logging.html#logging-levels) .<br />The default value is `INFO`. |
| **MWI_LOG_FILE** | string | `"/tmp/logs.txt"` | Specify the full path to the file where you want debug logs from this integration to be written. |
| **MWI_WEB_LOGGING_ENABLED** | string | `"True"` | Set this value to `"true"` to see additional web server logs. |
| **MWI_CUSTOM_HTTP_HEADERS** | string  |`'{"Content-Security-Policy": "frame-ancestors *.example.com:*"}'`<br /> OR <br />`"/path/to/your/custom/http-headers.json"` |Specify valid HTTP headers as JSON data in a string format. <br /> Alternatively, specify the full path to the JSON file containing valid HTTP headers instead. These headers are injected into the HTTP response sent to the browser. </br> For  more information, see the [Custom HTTP Headers](#custom-http-headers) section.|
| **TMPDIR** or **TMP** | string | `"/path/for/MATLAB/to/use/as/tmp"` | Set either one of these variables to control the temporary folder used by MATLAB. `TMPDIR` takes precedence over `TMP` and if neither variable is set, `/tmp` is the default value used by MATLAB. |

## Usage outside of Jupyter environment

This package can be run outside of the Jupyter environment by executing the python console script
`matlab-jupyter-app`.

Execute this command on the machine in which MATLAB is installed with the environment variables `MWI_BASE_URL` and `MWI_APP_PORT` set as follows:
```bash
env MWI_BASE_URL="/my_base_url" MWI_APP_PORT=8080 matlab-jupyter-app
```

You can then access the web server on the link
```html
http://localhost:8080/my_base_url/index.html
```

These environment variables are implicitly set by the Jupyter environment, and 
you do not need to set them when accessing the integration through Jupyter. 

## Custom HTTP Headers 
If the web browser renders the MATLAB Integration for Jupyter with some other content, then the browser could block the integration because of mismatch of `Content-Security-Policy` header in the response headers from the integration.
To avoid this, provide custom HTTP headers. This allows browsers to load the content.

For example, if this integration is rendered along with some other content on the domain `www.example.com`, to allow the browser to load the content, create a JSON file of the following form:

```json
{
  "Content-Security-Policy": "frame-ancestors *.example.com:* https://www.example.com:*;"
}
```
Specify the full path to this sample file in the environment variable `MWI_CUSTOM_HTTP_HEADERS`.
Alternatively, if you want to specify the custom HTTP headers as a string in the environment variable, in a bash shell type a command of the form below:

```bash
export MWI_CUSTOM_HTTP_HEADERS='{"Content-Security-Policy": "frame-ancestors *.example.com:* https://www.example.com:*;"}'
```

If you add the `frame-ancestors` directive, the browser does not block the content of this integration hosted on the domain `www.example.com`.


For more information about `Content-Security-Policy` header,  check the [Mozilla developer docs for Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy).

**NOTE**: Setting custom HTTP headers is an advanced operation, only use this functionality if you are familiar with HTTP headers.
