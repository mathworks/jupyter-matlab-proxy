# Copyright 2023-2024 The MathWorks, Inc.

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
import os
from pathlib import Path
from tempfile import mkdtemp
import jupyterlab

# Allow JupyterLab to be started as root user
c.ServerApp.allow_root = True

# Listen on all IP Addresses - JLab defaults to only allowing requests from localhost.
c.ServerApp.ip = "0.0.0.0"

# Set the port to serve JupyterLab on.
c.ServerApp.port = int(os.getenv("TEST_JMP_PORT", 8888))

# Disable port retries
c.ServerApp.port_retries = 0

# Disable opening the browser automatically
c.ServerApp.open_browser = False

# Set the root directory for the Jupyter server to a temporary directory
c.ServerApp.root_dir = mkdtemp(prefix="galata-test-")

# Enabling Galata for JupyterLab 4
c.LabApp.extra_labextensions_path = str(Path(jupyterlab.__file__).parent / "galata")

# Disable token-based authentication
c.IdentityProvider.token = ""

# Disable password-based authentication
c.IdentityProvider.password = ""

# Disable Cross-Site Request Forgery (CSRF) protection
c.ServerApp.disable_check_xsrf = True

# Expose the JupyterLab application in the browser
c.LabApp.expose_app_in_browser = True

# Set the log level to ERROR
c.Application.log_level = "INFO"
