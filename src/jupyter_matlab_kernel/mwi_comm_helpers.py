# Copyright 2023-2024 The MathWorks, Inc.
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

    async def _send_eval_request_to_matlab(self, http_client, mcode):
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
        else:
            self.logger.error("Error during communication with matlab-proxy")
            raise resp.raise_for_status()

    async def _send_jupyter_request_to_matlab(self, request_type, inputs, http_client):
        execution_request_type = "feval"

        inputs.insert(0, request_type)
        inputs.insert(1, execution_request_type)

        self.logger.debug(
            f"Using {execution_request_type} request type for communication with EC"
        )

        if execution_request_type == "feval":
            resp = await self._send_feval_request_to_matlab(
                http_client, "processJupyterKernelRequest", 1, *inputs
            )
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
            resp = await self._send_eval_request_to_matlab(http_client, eval_mcode)

        return resp
