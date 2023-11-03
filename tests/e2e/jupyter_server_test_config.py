# Copyright 2023 The MathWorks, Inc.

"""
JupyterLab Configuration

This file contains the configuration options for customizing JupyterLab and the
Jupyter server. The options include disabling authentication, setting the root
directory, log level, and more.

Please review and modify the configuration options as needed to suit your
requirements.
See all configuration options available here:
https://jupyter-server.readthedocs.io/en/latest/other/full-config.html

Note that 'c' below is an instance of Jupyter's configuration class. This file
is parsed by Jupyter and the below modifications to configuration class are
applied.
"""


from tempfile import mkdtemp


# Disable port retries
c.ServerApp.port_retries = 0

# Disable opening the browser automatically
c.ServerApp.open_browser = False

# Set the root directory for the Jupyter server to a temporary directory
c.ServerApp.root_dir = mkdtemp(prefix="galata-test-")

# Disable token-based authentication
c.ServerApp.token = ""

# Disable password-based authentication
c.ServerApp.password = ""

# Disable Cross-Site Request Forgery (CSRF) protection
c.ServerApp.disable_check_xsrf = True

# Expose the JupyterLab application in the browser
c.LabApp.expose_app_in_browser = True

# Set the log level to ERROR
c.Application.log_level = "ERROR"
