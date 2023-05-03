# Copyright 2023 The MathWorks, Inc.
# Implementation of MATLAB Kernel

# Import Python Standard Library
import os
import sys
import time

# Import Dependencies
import ipykernel.kernelbase
import psutil
import requests
from requests.exceptions import HTTPError

from jupyter_matlab_kernel import mwi_comm_helpers


class MATLABConnectionError(Exception):
    """
    A connection error occurred while connecting to MATLAB.

    Args:
        message (string): Error message to be displayed
    """

    def __init__(self, message=None):
        if message is None:
            message = 'Error connecting to MATLAB. Check the status of MATLAB by clicking the "Open MATLAB" button. Retry after ensuring MATLAB is running successfully'
        super().__init__(message)


def start_matlab_proxy():
    """
    Start matlab-proxy registered with the jupyter server which started the
    current kernel process.

    Raises:
        MATLABConnectionError: Occurs when kernel is not started by jupyter server.
        HTTPError: Occurs when kernel cannot connect with matlab-proxy.

    Returns:
        Tuple (string, string, dict):
            url (string): Complete URL to send HTTP requests to matlab-proxy
            base_url (string): Complete base url for matlab-proxy provided by jupyter server
            headers (dict): HTTP headers required while sending HTTP requests to matlab-proxy
    """

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
    jupyter_server_pid = os.getppid()

    # On Windows platforms using venv/virtualenv an intermediate python process spaws the kernel.
    # jupyter_server ---spawns---> intermediate_process ---spawns---> jupyter_matlab_kernel
    # Thus we need to go one level higher to acquire the process id of the jupyter server.
    # Note: conda environments do not require this, and for these environments sys.prefix == sys.base_prefix
    is_virtual_env = sys.prefix != sys.base_prefix
    if sys.platform == "win32" and is_virtual_env:
        jupyter_server_pid = psutil.Process(jupyter_server_pid).ppid()

    nb_server = dict()
    found_nb_server = False
    for server in nb_server_list:
        if server["pid"] == jupyter_server_pid:
            found_nb_server = True
            nb_server = server
            # Stop iterating over the server list
            break

    # Verify that Password is disabled
    if nb_server["password"] is True:
        # TODO: To support passwords, we either need to acquire it from Jupyter or ask the user?
        raise MATLABConnectionError(
            """
            Error: MATLAB Kernel could not communicate with MATLAB.\n
            Reason: There is a password set to access the Jupyter server.\n
            Resolution: Delete the cached Notebook password file, and restart the kernel.\n
            See https://jupyter-notebook.readthedocs.io/en/stable/public_server.html#securing-a-notebook-server for more information.
            """
        )

    # Error out if the server is not found!
    if found_nb_server == False:
        raise MATLABConnectionError(
            """
            Error: MATLAB Kernel for Jupyter was unable to find the notebook server from which it was spawned!\n
            Resolution: Please relaunch kernel from JupyterLab or Classic Jupyter Notebook.
            """
        )

    url = "{protocol}://localhost:{port}{base_url}matlab".format(
        protocol="https" if nb_server["secure"] else "http",
        port=nb_server["port"],
        base_url=nb_server["base_url"],
    )

    # Fetch JupyterHub API token for HTTP request authentication
    # incase the jupyter server is started by JupyterHub.
    jh_api_token = os.getenv("JUPYTERHUB_API_TOKEN")

    # set the token to be used during communication with Jupyter
    # In environments where tokens are set for both nb_server & JupyterHub
    # precedence is given to the nb_server token
    if nb_server["token"]:
        token = nb_server["token"]
    elif jh_api_token:
        token = jh_api_token
    else:
        token = None

    if token:
        headers = {
            "Authorization": f"token {token}",
        }
    else:
        headers = None

    # This is content that is present in the matlab-proxy index.html page which
    # can be used to validate a proper response.
    matlab_proxy_index_page_identifier = "MWI_MATLAB_PROXY_IDENTIFIER"

    # send request to the matlab-proxy endpoint to make sure it is available.
    # If matlab-proxy is not started, jupyter-server starts it at this point.
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == requests.codes.OK:
        # Verify that the returned value is correct
        if matlab_proxy_index_page_identifier not in resp.text:
            raise MATLABConnectionError(
                """
                Error: MATLAB Kernel could not communicate with MATLAB.
                Reason: Possibly due to invalid jupyter security tokens.
                """
            )
        return url, nb_server["base_url"], headers
    else:
        resp.raise_for_status()


class MATLABKernel(ipykernel.kernelbase.Kernel):
    # Required variables for Jupyter Kernel to function
    # banner is shown only for Jupyter Console.
    banner = "MATLAB"
    implementation = "jupyter_matlab_kernel"
    implementation_version: str = "0.0.1"

    # Values should be same as Codemirror mode
    language_info = {
        "name": "matlab",
        "mimetype": "text/x-matlab",
        "file_extension": ".m",
    }

    # MATLAB Kernel state
    is_matlab_licensed: bool = False
    matlab_status = ""
    matlab_proxy_has_error: bool = False
    server_base_url = ""
    headers = dict()
    startup_error = None
    startup_checks_completed: bool = False

    def __init__(self, *args, **kwargs):
        # Call superclass constructor to initialize ipykernel infrastructure
        super(MATLABKernel, self).__init__(*args, **kwargs)
        try:
            # Start matlab-proxy using the jupyter-matlab-proxy registered endpoint
            self.murl, self.server_base_url, self.headers = start_matlab_proxy()
            (
                self.is_matlab_licensed,
                self.matlab_status,
                self.matlab_proxy_has_error,
            ) = mwi_comm_helpers.fetch_matlab_proxy_status(self.murl, self.headers)
        except (MATLABConnectionError, HTTPError) as err:
            self.startup_error = err

    # ipykernel Interface API
    # https://ipython.readthedocs.io/en/stable/development/wrapperkernels.html

    async def interrupt_request(self, stream, ident, parent):
        """
        Custom handling of interrupt request sent by Jupyter. For more info, look at
        https://jupyter-client.readthedocs.io/en/stable/messaging.html#kernel-interrupt
        """
        try:
            # Send interrupt request to MATLAB
            mwi_comm_helpers.send_interrupt_request_to_matlab(self.murl, self.headers)

            # Set the response to interrupt request.
            content = {"status": "ok"}
        except Exception as e:
            # Set the exception information as response to interrupt request
            content = {
                "status": "error",
                "ename": str(type(e).__name__),
                "evalue": str(e),
                "traceback": [],
            }

        self.session.send(stream, "interrupt_reply", content, parent, ident=ident)

    def do_execute(
        self,
        code,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=False,
        *,
        cell_id=None,
    ):
        """
        Used by ipykernel infrastructure for execution. For more info, look at
        https://jupyter-client.readthedocs.io/en/stable/messaging.html#execute
        """
        try:
            # Complete one-time startup checks before sending request to MATLAB.
            # Blocking call, returns after MATLAB is started.
            if not self.startup_checks_completed:
                self.perform_startup_checks()
                self.display_output(
                    {
                        "type": "stream",
                        "content": {
                            "name": "stdout",
                            "text": "Executing ...",
                        },
                    }
                )
                self.startup_checks_completed = True

            # Perform execution and categorization of outputs in MATLAB. Blocks
            # until execution results are received from MATLAB.
            outputs = mwi_comm_helpers.send_execution_request_to_matlab(
                self.murl, self.headers, code
            )

            # Clear the output area of the current cell. This removes any previous
            # outputs before publishing new outputs.
            self.display_output({"type": "clear_output", "content": {"wait": False}})

            # Display all the outputs produced during the execution of code.
            for data in outputs:
                # Ignore empty values returned from MATLAB.
                if not data:
                    continue
                self.display_output(data)
        except Exception as e:
            if isinstance(e, HTTPError):
                # If exception is an HTTPError, it means MATLAB is unavailable.
                # Replace the HTTPError with MATLABConnectionError to give
                # meaningful error message to the user
                e = MATLABConnectionError()

                # Since MATLAB is not available, we need to perform the startup
                # checks for subsequent execution requests
                self.startup_checks_completed = False

            # Send the exception message to the user.
            self.display_output({"type": "clear_output", "content": {"wait": False}})
            self.display_output(
                {
                    "type": "stream",
                    "content": {
                        "name": "stderr",
                        "text": str(e),
                    },
                }
            )
        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }

    def do_complete(self, code, cursor_pos):
        """
        Used by ipykernel infrastructure for tab completion. For more info, look
        at https://jupyter-client.readthedocs.io/en/stable/messaging.html#completion

        Note: Apart from completion results, no other data can be presented to
              user. For example, if matlab-proxy is not licensed, we cannot show
              the licensing window.
        """
        # Default completion results. It is modelled after ipkernel.py#do_complete
        # implementation to provide metadata for JupyterLab.
        completion_results = {
            "matches": [],
            "start": cursor_pos,
            "end": cursor_pos,
            "completions": [],
        }

        # Fetch tab completion results. Blocks untils either tab completion
        # results are received from MATLAB or communication with MATLAB fails.
        try:
            completion_results = mwi_comm_helpers.send_completion_request_to_matlab(
                self.murl, self.headers, code, cursor_pos
            )
        except HTTPError as e:
            pass

        return {
            "status": "ok",
            "matches": completion_results["matches"],
            "cursor_start": completion_results["start"],
            "cursor_end": completion_results["end"],
            "metadata": {
                "_jupyter_types_experimental": completion_results["completions"]
            },
        }

    def do_is_complete(self, code):
        # TODO: Seems like indentation rules. https://jupyter-client.readthedocs.io/en/stable/messaging.html#code-completeness
        return super().do_is_complete(code)

    def do_inspect(self, code, cursor_pos, detail_level=0, omit_sections=...):
        # TODO: Implement Shift+Tab functionality. Can be used to provide any contextual information.
        return super().do_inspect(code, cursor_pos, detail_level, omit_sections)

    def do_history(
        self,
        hist_access_type,
        output,
        raw,
        session=None,
        start=None,
        stop=None,
        n=None,
        pattern=None,
        unique=False,
    ):
        # TODO: Implement accessing history in Notebook. Usually this history is related to the code typed in notebook.
        # However, we may also choose to associate with MATLAB History stored on disk.
        return super().do_history(
            hist_access_type, output, raw, session, start, stop, n, pattern, unique
        )

    def do_shutdown(self, restart):
        # TODO: Implement clean-up
        return super().do_shutdown(restart)

    # Helper functions

    def perform_startup_checks(self):
        """
        One time checks triggered during the first execution request. Displays
        login window if matlab is not licensed using matlab-proxy.

        Raises:
            HTTPError, MATLABConnectionError: Occurs when matlab-proxy is not started or kernel cannot
                                              communicate with MATLAB.
        """
        # Incase an error occurred while kernel initialization, display it to the user.
        if self.startup_error is not None:
            raise self.startup_error

        (
            self.is_matlab_licensed,
            self.matlab_status,
            self.matlab_proxy_has_error,
        ) = mwi_comm_helpers.fetch_matlab_proxy_status(self.murl, self.headers)

        # Display iframe containing matlab-proxy to show login window if MATLAB
        # is not licensed using matlab-proxy. The iframe is removed after MATLAB
        # has finished startup.
        #
        # This approach does not work when using the kernel in VS Code. We are using relative path
        # as src for iframe to avoid hardcoding any hostname/domain information. This is done to
        # ensure the kernel works in Jupyter deployments. VS Code however does not work the same way
        # as other browser based Jupyter clients.
        #
        # TODO: Find a workaround for users to be able to use our Jupyter kernel in VS Code.
        if not self.is_matlab_licensed:
            self.display_output(
                {
                    "type": "display_data",
                    "content": {
                        "data": {
                            "text/html": f'<iframe src={self.server_base_url + "matlab"} width=700 height=600"></iframe>'
                        },
                        "metadata": {},
                    },
                }
            )

        # Wait until MATLAB is started before sending requests.
        timeout = 0
        while (
            self.matlab_status != "up"
            and timeout != 15
            and not self.matlab_proxy_has_error
        ):
            if self.is_matlab_licensed:
                if timeout == 0:
                    self.display_output(
                        {"type": "clear_output", "content": {"wait": False}}
                    )
                    self.display_output(
                        {
                            "type": "stream",
                            "content": {
                                "name": "stdout",
                                "text": f"Starting MATLAB ...\n",
                            },
                        }
                    )
                timeout += 1
            time.sleep(1)
            (
                self.is_matlab_licensed,
                self.matlab_status,
                self.matlab_proxy_has_error,
            ) = mwi_comm_helpers.fetch_matlab_proxy_status(self.murl, self.headers)

        # If MATLAB is not available after 15 seconds of licensing information
        # being available either through user input or through matlab-proxy cache,
        # then display connection error to the user.
        if timeout == 15 or self.matlab_proxy_has_error:
            raise MATLABConnectionError

    def display_output(self, out):
        """
        Common function to send execution outputs to Jupyter UI.
        For more information, look at https://jupyter-client.readthedocs.io/en/stable/messaging.html#messages-on-the-iopub-pub-sub-channel

        Input Example:
        1.  Execution Output:
            out = {
                "type": "execute_result",
                "mimetype": ["text/plain","text/html"],
                "value": ["Hello","<html><body>Hello</body></html>"]
            }
        2.  For all other message types:
            out = {
                "type": "stream",
                "content": {
                    "name": "stderr",
                    "text": "An error occurred"
                }
            }

        Args:
            out (dict): A dictionary containing the type of output and the content of the output.
        """
        msg_type = out["type"]
        if msg_type == "execute_result":
            assert len(out["mimetype"]) == len(out["value"])
            response = {
                # Use zip to create a tuple of KV pair of mimetype and value.
                "data": dict(zip(out["mimetype"], out["value"])),
                "metadata": {},
                "execution_count": self.execution_count,
            }
        else:
            response = out["content"]
        self.send_response(self.iopub_socket, msg_type, response)
