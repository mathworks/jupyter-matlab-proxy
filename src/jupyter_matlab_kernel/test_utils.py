# Copyright 2023-2024 The MathWorks, Inc.

import os
from jupyter_matlab_kernel import mwi_logger

_logger = mwi_logger.get()


def is_jupyter_testing_enabled():
    """
    Checks if testing mode is enabled

    Returns:
        bool: True if MWI_JUPYTER_TEST environment variable is set to 'true'
        else False
    """

    return os.environ.get("MWI_JUPYTER_TEST", "false").lower() == "true"


def start_matlab_proxy_for_testing(logger=_logger):
    """
    Only used for testing purposes. Gets the matlab-proxy server configuration
    from environment variables and mocks the 'start_matlab_proxy' function

    Returns:
        Tuple (string, string, dict):
            url (string): Complete URL to send HTTP requests to matlab-proxy
            base_url (string): Complete base url for matlab-proxy obtained from tests
            headers (dict): Empty dictionary
    """

    import matlab_proxy.util.mwi.environment_variables as mwi_env

    # These environment variables are being set by tests, using dictionary lookup
    # instead of '.getenv' to make sure that the following line fails with the
    # Exception 'KeyError' in case the environment variables are not set
    matlab_proxy_base_url = os.environ[mwi_env.get_env_name_base_url()]
    matlab_proxy_app_port = os.environ[mwi_env.get_env_name_app_port()]

    logger.debug("Creating matlab-proxy URL for MATLABKernel testing.")

    # '127.0.0.1' is used instead 'localhost' for testing since Windows machines consume
    # some time to resolve 'localhost' hostname
    url = "{protocol}://127.0.0.1:{port}{base_url}".format(
        protocol="http",
        port=matlab_proxy_app_port,
        base_url=matlab_proxy_base_url,
    )
    headers = {}

    logger.debug("matlab-proxy URL: %s", url)
    logger.debug("headers: %s", headers)

    return url, matlab_proxy_base_url, headers
