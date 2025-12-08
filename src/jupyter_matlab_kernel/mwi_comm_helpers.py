# Copyright 2023-2025 The MathWorks, Inc.
# Helper functions to communicate with matlab-proxy and MATLAB

import http
import json
import pathlib

import aiohttp
from matlab_proxy.util.mwi.embedded_connector.helpers import (
    get_data_to_eval_mcode,
    get_data_to_feval_mcode,
    get_mvm_endpoint,
)

from jupyter_matlab_kernel import mwi_logger
from jupyter_matlab_kernel.mwi_exceptions import MATLABConnectionError

_logger = mwi_logger.get()


def check_licensing_status(data):
    licensing_status = data["licensing"] is not None

    # Check for entitlementId only in the event of online licensing
    if licensing_status and data["licensing"]["type"] == "mhlm":
        licensing_status = data["licensing"]["entitlementId"] is not None
    return licensing_status


class MWICommHelper:
    def __init__(
        self, kernel_id, url, shell_loop, control_loop, headers=None, logger=_logger
    ) -> None:
        """_summary_

        Args:
            kernel_id (str): Unique identifier corresponding to the Jupyter kernel instance.
            url (str): URL of the matlab-proxy server.
            shell_loop : event loop corresponding to the Shell channel in Jupyter Messaging Protocol
            control_loop : event loop corresponding to the Control channel in Jupyter Messaging Protocol
            headers (dict, optional): Headers containing auth information for communication with matlab-proxy server. Defaults to None.
            logger (Logger, optional): Instance of Logger. Defaults to _logger.
        """
        self.kernel_id = kernel_id
        self.url = url
        self._shell_loop = shell_loop
        self._control_loop = control_loop
        self.headers = headers
        self.logger = logger
        self._http_shell_client = None
        self._http_control_client = None

    async def _create_http_session(self, loop):
        """Helper function to create a aiohttp ClientSession which uses a given asyncio event loop

        Args:
            loop : asyncio event loop

        Returns:
            ClientSession : aiohttp ClientSession with disabled timeouts and required headers.
        """
        # Disable timeout as the execution of MATLAB code might be longer.
        timeout = aiohttp.ClientTimeout(total=None)

        # Creation of ClientSession needs to be done in an async function. We cannot
        # specify base url as it may contain additional path (such as in jupyterhub.com/user/matlab)
        # which is not supported by ClientSession
        return aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False, loop=loop),
            headers=self.headers,
            trust_env=True,
            timeout=timeout,
        )

    async def connect(self):
        """Initializes the HTTP clients"""
        if self._http_shell_client is None:
            self._http_shell_client = await self._create_http_session(self._shell_loop)

        if self._http_control_client is None:
            self._http_control_client = await self._create_http_session(
                self._control_loop
            )

    async def disconnect(self):
        if self._http_shell_client:
            await self._http_shell_client.close()
        if self._http_control_client:
            await self._http_control_client.close()

    async def fetch_matlab_proxy_status(self):
        """
        Sends HTTP request to /get_status endpoint of matlab-proxy and returns
        license and MATLAB status.

        Returns:
            Tuple (bool, string):
                is_matlab_licensed (bool): True if matlab-proxy has license information, else False.
                matlab_status (string): Status of MATLAB. Values could be "up", "down" and "starting"
                matlab_proxy_has_error (bool): True if matlab-proxy faced any issues and unable to
                                               start MATLAB

        Raises:
            HTTPError: Occurs when connection to matlab-proxy cannot be established.
        """
        self.logger.debug("Fetching matlab-proxy status")
        resp = await self._http_shell_client.get(self.url + "/get_status")
        self.logger.debug(f"Received status code: {resp.status}")
        if resp.status == http.HTTPStatus.OK:
            data = await resp.json()
            self.logger.debug(f"Response:\n{data}")
            is_matlab_licensed = check_licensing_status(data)

            matlab_status = data["matlab"]["status"]
            matlab_proxy_has_error = data["error"] is not None
            return is_matlab_licensed, matlab_status, matlab_proxy_has_error
        else:
            self.logger.error("Error occurred during communication with matlab-proxy")
            resp.raise_for_status()

    async def send_execution_request_to_matlab(self, code):
        """
        Evaluate MATLAB code and capture results.

        Args:
            code (string): MATLAB code to be evaluated

        Returns:
            List(dict): list of outputs captured during evaluation.

        Raises:
            HTTPStatusError: Occurs when connection to matlab-proxy cannot be established.
        """
        self.logger.debug("Sending execution request to MATLAB")
        return await self._send_jupyter_request_to_matlab(
            "execute", [code, self.kernel_id], self._http_shell_client
        )

    async def send_completion_request_to_matlab(self, code, cursor_pos):
        """
        Fetch Tab completion results.

        Args:
            code (string): MATLAB code on which Tab completion is requested.
            cursor_pos (int): Position of the cursor when Tab completion is requested.

        Returns:
            Dict: Tab completion results similar to ipykernel's do_complete method.
                  Example: {
                    "matches": ["plot"],
                    "start": 0,
                    "end": 3,
                    "completions": [{
                        "type": "function",
                        "text": "plot",
                        "start": 0,
                        "end": 3
                    }]
                  }

        Raises:
            HTTPError: Occurs when connection to matlab-proxy cannot be established.
        """
        self.logger.debug("Sending completion request to MATLAB")
        return await self._send_jupyter_request_to_matlab(
            "complete", [code, cursor_pos], self._http_shell_client
        )

    async def send_shutdown_request_to_matlab(self):
        """
        Perform cleanup tasks related to kernel shutdown.

        Raises:
            HTTPError: Occurs when connection to matlab-proxy cannot be established.
        """
        self.logger.debug("Sending shutdown request to MATLAB")
        return await self._send_jupyter_request_to_matlab(
            "shutdown", [self.kernel_id], self._http_control_client
        )

    async def send_interrupt_request_to_matlab(self):
        """Send an interrupt request to MATLAB to stop current execution.

        The interrupt request is sent through the control channel using a specific message format.

        Raises:
            HTTPError: If the interrupt request fails or matlab-proxy communication errors occur
        """
        self.logger.debug("Sending interrupt request to MATLAB")
        req_body = {
            "messages": {
                "Interrupt": [
                    {
                        "uuid": "1234",
                    }
                ]
            }
        }
        url = get_mvm_endpoint(self.url)

        self.logger.debug(f"Request URL: {url}")
        self.logger.debug(f"Request Headers:\n{self.headers}")
        self.logger.debug(f"Request Body:\n{req_body}")
        resp = await self._http_control_client.post(url, json=req_body)
        self.logger.debug(f"Received status code: {resp.status}")
        if resp.status != http.HTTPStatus.OK:
            self.logger.error("Error occurred during communication with matlab-proxy")
            resp.raise_for_status()

    async def _send_feval_request_to_matlab(self, http_client, fname, nargout, *args):
        """Execute a MATLAB function call (feval) through the matlab-proxy.

        Sends a function evaluation request to MATLAB, handling path setup and synchronous execution.

        Args:
            http_client (aiohttp.ClientSession): HTTP client for sending the request
            fname (str): Name of the MATLAB function to call
            nargout (int): Number of output arguments expected
            *args: Variable arguments to pass to the MATLAB function

        Returns:
            list: Results from the MATLAB function execution if successful
                 Empty list if no outputs or nargout=0

        Raises:
            MATLABConnectionError: If MATLAB connection is lost or response is invalid
            Exception: If function execution fails or is interrupted by user
        """
        self.logger.debug("Sending FEval request to MATLAB")
        # Add the MATLAB code shipped with kernel to the Path
        path = [str(pathlib.Path(__file__).parent / "matlab")]
        req_body = get_data_to_feval_mcode("addpath", *path, nargout=0)
        original_request = get_data_to_feval_mcode(fname, *args, nargout=nargout)

        # Add the FEval message of original request to the req_body FEval list.
        req_body["messages"]["FEval"].append(original_request["messages"]["FEval"][0])

        # Set the deque mode to make execution synchronous.
        req_body["messages"]["FEval"][0]["dequeMode"] = "non_debug_prompt"
        req_body["messages"]["FEval"][1]["dequeMode"] = "non_debug_prompt"

        url = get_mvm_endpoint(self.url)

        self.logger.debug(f"Request URL: {url}")
        self.logger.debug(f"Request Headers:\n{self.headers}")
        self.logger.debug(f"Request Body:\n{req_body}")

        resp = await http_client.post(
            url,
            json=req_body,
        )
        self.logger.debug(f"Received status code: {resp.status}")
        if resp.status == http.HTTPStatus.OK:
            response_data = await resp.json()
            self.logger.debug(f"Response:\n{response_data}")
            try:
                feval_response = response_data["messages"]["FEvalResponse"][1]
            except KeyError:
                # In certain cases when the HTTPResponse is received, it does not
                # contain the expected data. In these cases most likely MATLAB has
                # gone away. Hence we raise the HTTPError to indicate MATLAB is not
                # available.
                self.logger.error(
                    "Response messages doesn't contain FEvalResponse field"
                )
                raise MATLABConnectionError()

            # If the feval request succeeded and outputs are present, return the result.
            if not feval_response["isError"]:
                if nargout != 0 and feval_response["results"]:
                    return feval_response["results"][0]

                self.logger.debug("No result present in FEvalResponse")
                # Return empty list if there are no outputs in the repsonse
                return []

            # Handle error case. This happens when "Interrupt Kernel" is issued.
            if feval_response["messageFaults"][0]["message"] == "":
                error_message = (
                    "Failed to execute. Operation may have interrupted by user."
                )
            else:
                self.logger.error(
                    f'Error during execution of FEval request in MATLAB:\n{feval_response["messageFaults"][0]["message"]}'
                )
                error_message = "Failed to execute. Please try again."
            raise Exception(error_message)
        else:
            self.logger.error("Error occurred during communication with matlab-proxy")
            raise resp.raise_for_status()

    async def send_eval_request_to_matlab(self, mcode):
        """Send an evaluation request to MATLAB using the shell client.

        Args:
            mcode (str): MATLAB code to be evaluated

        Returns:
            dict: The evaluation response from MATLAB containing results or error information

        Raises:
            MATLABConnectionError: If MATLAB connection is not available
            HTTPError: If there is an error in communication with matlab-proxy
        """
        return await self._send_eval_request_to_matlab(self._http_shell_client, mcode)

    async def _send_eval_request_to_matlab(self, http_client, mcode):
        """Internal method to send and process an evaluation request to MATLAB.

        Args:
            http_client (aiohttp.ClientSession): HTTP client to use for the request
            mcode (str): MATLAB code to be evaluated

        Returns:
            dict: The evaluation response containing results or error information
                 from the MATLAB execution

        Raises:
            MATLABConnectionError: If MATLAB connection is not available or response is invalid
            HTTPError: If there is an error in communication with matlab-proxy
        """
        self.logger.debug("Sending Eval request to MATLAB")
        # Add the MATLAB code shipped with kernel to the Path
        path = str(pathlib.Path(__file__).parent / "matlab")
        mcode = 'addpath("' + path + '")' + ";" + mcode

        req_body = get_data_to_eval_mcode(mcode)
        url = get_mvm_endpoint(self.url)

        self.logger.debug(f"Request URL: {url}")
        self.logger.debug(f"Request Headers:\n{self.headers}")
        self.logger.debug(f"Request Body:\n{req_body}")
        resp = await http_client.post(
            url,
            json=req_body,
        )
        self.logger.debug(f"Received status code: {resp.status}")
        if resp.status == http.HTTPStatus.OK:
            response_data = await resp.json()
            self.logger.debug(f"Response:\n{response_data}")
            try:
                eval_response = response_data["messages"]["EvalResponse"][0]

            except KeyError:
                # In certain cases when the HTTPResponse is received, it does not
                # contain the expected data. In these cases most likely MATLAB has
                # gone away. Hence we raise the HTTPError to indicate MATLAB is not
                # available.
                self.logger.error(
                    "Response messages doesn't contain EvalResponse field"
                )
                raise MATLABConnectionError()

            return eval_response

        else:
            self.logger.error("Error during communication with matlab-proxy")
            raise resp.raise_for_status()

    async def _send_jupyter_request_to_matlab(self, request_type, inputs, http_client):
        """Process and send a Jupyter request to MATLAB using either feval or eval execution.

        Args:
            request_type (str): Type of request (execute, complete, shutdown)
            inputs (list): List of input arguments for the request
            http_client (aiohttp.ClientSession): HTTP client to use for the request

        Returns:
            dict: Response from MATLAB containing results of the request execution

        Raises:
            MATLABConnectionError: If MATLAB connection is not available
            Exception: If request execution fails or is interrupted
        """
        execution_request_type = "feval"

        inputs.insert(0, request_type)
        inputs.insert(1, execution_request_type)

        self.logger.debug(
            f"Using {execution_request_type} request type for communication with EC"
        )

        resp = None
        if execution_request_type == "feval":
            resp = await self._send_feval_request_to_matlab(
                http_client, "processJupyterKernelRequest", 1, *inputs
            )

        # The 'else' condition is an artifact and is present here incase we ever want to test
        # eval execution.
        else:
            user_mcode = inputs[2]
            # Construct a string which can be evaluated in MATLAB. For example
            # "processJupyterKernelRequest('execute', 'eval', 'a = "Hello\\n''world''"')".
            # To achieve this, we need to replace the single-quotes with two single-quotes,
            # so that MATLAB can properly recognize the single-quotes present in user
            # code. Also, we need to escape the backslash (\) character so that the
            # string which needs to be evaluated isn't broken down by MATLAB due to
            # formatting
            args = (
                f"'{request_type}', '{execution_request_type}', '"
                + json.dumps(user_mcode.replace("'", "''"))
                + "'"
            )
            if request_type == "complete":
                cursor_pos = inputs[3]
                args = args + "," + str(cursor_pos)

            eval_mcode = f"processJupyterKernelRequest({args})"
            eval_response = await self._send_eval_request_to_matlab(
                http_client, eval_mcode
            )
            resp = await self._read_eval_response_from_file(eval_response)

        return resp

    async def _read_eval_response_from_file(self, eval_response):
        """Read and process MATLAB evaluation results from a response file.

        Args:
            eval_response (dict): Response dictionary from MATLAB eval request containing
                                file path and error information

        Returns:
            dict: JSON decoded results from the response file

        Raises:
            Exception: If evaluation failed or was interrupted by user
        """
        # If the eval request succeeded, return the json decoded result.
        if not eval_response["isError"]:
            result_filepath = eval_response["responseStr"].strip()

            # If the filepath in the response is not empty, read the result from
            # file and delete the file.
            if result_filepath != "":
                self.logger.debug(f"Found file with results: {result_filepath}")
                self.logger.debug("Reading contents of the file")
                with open(result_filepath, "r") as f:
                    result = f.read().strip()
                self.logger.debug("Reading completed")
                try:
                    import os

                    self.logger.debug(f"Deleting file: {result_filepath}")
                    os.remove(result_filepath)
                except Exception:
                    self.logger.error("Deleting file failed")
            else:
                self.logger.debug("No result in EvalResponse")
                result = ""

            # If result is empty, populate dummy json
            if result == "":
                result = "[]"
            return json.loads(result)

        # Handle the error cases
        if eval_response["messageFaults"]:
            # This happens when "Interrupt Kernel" is issued from a different
            # kernel. There may be other cases also.
            self.logger.error(
                f'Error during execution of Eval request in MATLAB:\n{eval_response["messageFaults"][0]["message"]}'
            )
            error_message = (
                "Failed to execute. Operation may have been interrupted by user."
            )
        else:
            # This happens when "Interrupt Kernel" is issued from the same kernel.
            # The responseStr contains the error message
            error_message = eval_response["responseStr"].strip()
        raise Exception(error_message)
