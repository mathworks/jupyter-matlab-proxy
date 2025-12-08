# Copyright 2024-2025 The MathWorks, Inc.

"""This module contains derived class implementation of MATLABKernel that uses
Jupyter Server to manage interactions with matlab-proxy & MATLAB.
"""

import asyncio
import http
import os

# Import Dependencies
import aiohttp
import aiohttp.client_exceptions
import requests

from jupyter_matlab_kernel import base_kernel as base
from jupyter_matlab_kernel import mwi_logger, test_utils
from jupyter_matlab_kernel.mwi_comm_helpers import MWICommHelper
from jupyter_matlab_kernel.mwi_exceptions import MATLABConnectionError

_logger = mwi_logger.get()


def _start_matlab_proxy_using_jupyter(url, headers, logger=_logger):
    """
    Start matlab-proxy using jupyter server which started the current kernel
    process by sending HTTP request to the endpoint registered through
    jupyter-matlab-proxy.

    Args:
        url (string): URL to send HTTP request
        headers (dict): HTTP headers required for the request

    Returns:
        bool: True if jupyter server has successfully started matlab-proxy else False.
    """
    # This is content that is present in the matlab-proxy index.html page which
    # can be used to validate a proper response.
    matlab_proxy_index_page_identifier = "MWI_MATLAB_PROXY_IDENTIFIER"

    logger.debug(
        f"Sending request to jupyter to start matlab-proxy at {url} with headers: {headers}"
    )
    # send request to the matlab-proxy endpoint to make sure it is available.
    # If matlab-proxy is not started, jupyter-server starts it at this point.
    resp = requests.get(url, headers=headers, verify=False)
    logger.debug("Received status code: %s", resp.status_code)

    return (
        resp.status_code == http.HTTPStatus.OK
        and matlab_proxy_index_page_identifier in resp.text
    )


def start_matlab_proxy(logger=_logger):
    """
    Start matlab-proxy registered with the jupyter server which started the
    current kernel process.

    Raises:
        MATLABConnectionError: Occurs when kernel is not started by jupyter server.

    Returns:
        Tuple (string, string, dict):
            url (string): Complete URL to send HTTP requests to matlab-proxy
            base_url (string): Complete base url for matlab-proxy provided by jupyter server
            headers (dict): HTTP headers required while sending HTTP requests to matlab-proxy
    """

    # If jupyter testing is enabled, then a standalone matlab-proxy server would be
    # launched by the tests and kernel would expect the configurations of this matlab-proxy
    # server which is provided through environment variables to 'start_matlab_proxy_for_testing'
    if test_utils.is_jupyter_testing_enabled():
        return test_utils.start_matlab_proxy_for_testing(logger)

    nb_server_list = []

    # The matlab-proxy server, if running, could have been started by either
    # "jupyter_server" or "notebook" package.
    try:
        from jupyter_server import serverapp

        nb_server_list += list(serverapp.list_running_servers())

        from notebook import notebookapp

        nb_server_list += list(notebookapp.list_running_servers())
    except ImportError:
        pass

    # Use parent process id of the kernel to filter Jupyter Server from the list.
    jupyter_server_pid = base._get_parent_pid()
    logger.debug(f"Resolved jupyter server pid: {jupyter_server_pid}")

    nb_server = dict()
    found_nb_server = False
    for server in nb_server_list:
        if server["pid"] == jupyter_server_pid:
            logger.debug("Jupyter server associated with this MATLAB Kernel found.")
            found_nb_server = True
            nb_server = server
            # Stop iterating over the server list
            break

    # Error out if the server is not found!
    if not found_nb_server:
        logger.error("Jupyter server associated with this MATLABKernel not found.")
        raise MATLABConnectionError(
            """
            Error: MATLAB Kernel for Jupyter was unable to find the notebook server from which it was spawned!\n
            Resolution: Please relaunch kernel from JupyterLab or Classic Jupyter Notebook.
            """
        )

    # Verify that Password is disabled
    if nb_server["password"] is True:
        logger.error("Jupyter server uses password for authentication.")
        # TODO: To support passwords, we either need to acquire it from Jupyter or ask the user?
        raise MATLABConnectionError(
            """
            Error: MATLAB Kernel could not communicate with MATLAB.\n
            Reason: There is a password set to access the Jupyter server.\n
            Resolution: Delete the cached Notebook password file, and restart the kernel.\n
            See https://jupyter-notebook.readthedocs.io/en/stable/public_server.html#securing-a-notebook-server for more information.
            """
        )

    # Using nb_server["url"] to construct matlab-proxy URL as it handles the following cases
    # 1. For normal usage of Jupyter, the URL returned by nb_server uses localhost
    # 2. For explicitly specified IP with Jupyter, the URL returned by nb_server
    #       a. uses FQDN hostname when specified IP is 0.0.0.0
    #       b. uses specified IP for all other cases
    matlab_proxy_url = "{jupyter_server_url}matlab".format(
        jupyter_server_url=nb_server["url"]
    )

    available_tokens = {
        "jupyter_server": nb_server.get("token"),
        "jupyterhub": os.getenv("JUPYTERHUB_API_TOKEN"),
        "default": None,
    }

    for token in available_tokens.values():
        if token:
            headers = {"Authorization": f"token {token}"}
        else:
            headers = None

        if _start_matlab_proxy_using_jupyter(matlab_proxy_url, headers, logger):
            logger.debug(
                f"Started matlab-proxy using jupyter at {matlab_proxy_url} with headers: {headers}"
            )
            return matlab_proxy_url, nb_server["base_url"], headers

    logger.error(
        "MATLABKernel could not communicate with matlab-proxy through Jupyter server"
    )
    logger.error(f"Jupyter server:\n{nb_server}")
    raise MATLABConnectionError(
        """
                Error: MATLAB Kernel could not communicate with MATLAB.
                Reason: Possibly due to invalid jupyter security tokens.
                """
    )


class MATLABKernelUsingJSP(base.BaseMATLABKernel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            # Start matlab-proxy using the jupyter-matlab-proxy registered endpoint.
            murl, self.jupyter_base_url, headers = start_matlab_proxy(self.log)

            # Using asyncio.get_event_loop for shell_loop as io_loop variable is
            # not yet initialized because start() is called after the __init__
            # is completed.
            shell_loop = asyncio.get_event_loop()
            control_loop = self.control_thread.io_loop.asyncio_loop
            self.mwi_comm_helper = MWICommHelper(
                self.kernel_id, murl, shell_loop, control_loop, headers, self.log
            )
            shell_loop.run_until_complete(self.mwi_comm_helper.connect())
        except MATLABConnectionError as err:
            self.startup_error = err

    async def do_shutdown(self, restart):
        self.log.debug("Received shutdown request from Jupyter")
        try:
            await self.mwi_comm_helper.send_shutdown_request_to_matlab()
            await self.mwi_comm_helper.disconnect()
        except (
            MATLABConnectionError,
            aiohttp.client_exceptions.ClientResponseError,
        ) as e:
            self.log.error(
                f"Exception occurred while sending shutdown request to MATLAB:\n{e}"
            )

        return super().do_shutdown(restart)

    async def perform_startup_checks(self):
        """Overriding base function to provide a different iframe source"""
        await super().perform_startup_checks(self.jupyter_base_url, "matlab")
