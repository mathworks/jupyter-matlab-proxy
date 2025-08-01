# Copyright 2024-2025 The MathWorks, Inc.

"""This module contains derived class implementation of MATLABKernel that uses
MATLAB Proxy Manager to manage interactions with matlab-proxy & MATLAB.
"""

from logging import Logger

import matlab_proxy_manager.lib.api as mpm_lib
from requests.exceptions import HTTPError

from jupyter_matlab_kernel import base_kernel as base
from jupyter_matlab_kernel.mwi_comm_helpers import MWICommHelper
from jupyter_matlab_kernel.mwi_exceptions import MATLABConnectionError


class MATLABKernelUsingMPM(base.BaseMATLABKernel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Used to detect if this Kernel has been assigned a MATLAB-proxy server or not
        self.is_matlab_assigned = False

        # Serves as the auth token to secure communication between Jupyter Server and MATLAB proxy manager
        self.mpm_auth_token = None

        # There might be multiple instances of Jupyter servers or VScode servers running on a
        # single machine. This attribute serves as the context provider and backend MATLAB proxy
        # processes are filtered using this attribute during start and shutdown of MATLAB proxy
        self.parent_pid = base._get_parent_pid()

        # Required for performing licensing using Jupyter Server
        self.jupyter_base_url = base._fetch_jupyter_base_url(self.parent_pid, self.log)

    # ipykernel Interface API
    # https://ipython.readthedocs.io/en/stable/development/wrapperkernels.html

    async def do_execute(
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
        self.log.debug(f"Received execution request from Jupyter with code:\n{code}")

        # Starts the matlab proxy process if this kernel hasn't yet been assigned a
        # matlab proxy and sets the attributes on kernel to talk to the correct backend.
        if not self.is_matlab_assigned:
            self.log.debug("Starting matlab-proxy")
            await self._start_matlab_proxy_and_comm_helper()
            self.is_matlab_assigned = True

        return await super().do_execute(
            code=code,
            silent=silent,
            store_history=store_history,
            user_expressions=user_expressions,
            allow_stdin=allow_stdin,
            cell_id=cell_id,
        )

    async def do_shutdown(self, restart):
        self.log.debug("Received shutdown request from Jupyter")
        if self.is_matlab_assigned:
            try:
                # Cleans up internal live editor state, client session
                await self.mwi_comm_helper.send_shutdown_request_to_matlab()
                await self.mwi_comm_helper.disconnect()

            except (MATLABConnectionError, HTTPError) as e:
                self.log.error(
                    f"Exception occurred while sending shutdown request to MATLAB:\n{e}"
                )
            except Exception as e:
                self.log.debug("Exception during shutdown", e)
            finally:
                # Shuts down matlab assigned to this Kernel (based on satisfying certain criteria)
                await mpm_lib.shutdown(
                    self.parent_pid, self.kernel_id, self.mpm_auth_token
                )
                self.is_matlab_assigned = False

        return super().do_shutdown(restart)

    async def perform_startup_checks(self):
        """Overriding base function to provide a different iframe source"""
        await super().perform_startup_checks(
            self.jupyter_base_url, f"{self.matlab_proxy_base_url}/"
        )

    # Helper functions

    async def _start_matlab_proxy_and_comm_helper(self) -> None:
        """
        Starts the MATLAB proxy using the proxy manager and fetches its status.
        """
        try:
            (
                murl,
                self.matlab_proxy_base_url,
                headers,
                self.mpm_auth_token,
            ) = await self._initialize_matlab_proxy_with_mpm(self.log)

            await self._initialize_mwi_comm_helper(murl, headers)
        except MATLABConnectionError as err:
            self.startup_error = err

    async def _initialize_matlab_proxy_with_mpm(self, _logger: Logger):
        """
        Initializes the MATLAB proxy process using the Proxy Manager (MPM) library.

        Calls proxy manager to start the MATLAB proxy process for this kernel.

        Args:
            logger (Logger): The logger instance

        Returns:
            tuple: A tuple containing:
                - server_url (str): Absolute URL for the MATLAB proxy backend (includes base URL)
                - base_url (str): The base URL of the MATLAB proxy server
                - headers (dict): The headers required for communication with the MATLAB proxy
                - mpm_auth_token (str): Token for authentication between kernel and proxy manager

        Raises:
            MATLABConnectionError: If the MATLAB proxy process could not be started
        """
        try:
            response = await mpm_lib.start_matlab_proxy_for_kernel(
                caller_id=self.kernel_id,
                parent_id=self.parent_pid,
                is_shared_matlab=True,
                base_url_prefix=self.jupyter_base_url,
            )
            err = response.get("errors")
            if err:
                raise MATLABConnectionError(err)
            return (
                response.get("absolute_url"),
                response.get("mwi_base_url"),
                response.get("headers"),
                response.get("mpm_auth_token"),
            )
        except Exception as e:
            _logger.error(f"MATLAB Kernel could not start matlab-proxy, Reason: {e}")
            raise MATLABConnectionError(
                f"""
                Error: MATLAB Kernel could not start the MATLAB proxy process.
                Reason: {e}
                Resolution: Run the troubleshooting script described in the file `troubleshooting.md`.
                If the issue persists, create an issue on Github: https://github.com/mathworks/jupyter-matlab-proxy/issues.
                """
            ) from e

    async def _initialize_mwi_comm_helper(self, murl, headers):
        """
        Initializes the MWICommHelper for managing communication with a specified URL.

        This method sets up the MWICommHelper instance with the given
        message URL and headers, utilizing the shell and control event loops. It then
        initiates a connection by creating and awaiting a task on the shell event loop.

        Parameters:
        - murl (str): The message URL used for communication.
        - headers (dict): A dictionary of headers to include in the communication setup.
        """
        shell_loop = self.io_loop.asyncio_loop
        control_loop = self.control_thread.io_loop.asyncio_loop
        self.mwi_comm_helper = MWICommHelper(
            self.kernel_id, murl, shell_loop, control_loop, headers, self.log
        )
        await self.mwi_comm_helper.connect()

    def _process_children(self):
        """Overrides the _process_children in kernelbase class to not return the list of children
        so that the child process termination can be managed at proxy manager layer
        """
        return []
