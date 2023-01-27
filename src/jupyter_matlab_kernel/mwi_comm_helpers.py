# Copyright 2023 The MathWorks, Inc.
# Helper functions to communicate with matlab-proxy and MATLAB

import json
import pathlib

import requests
from matlab_proxy.util.mwi.embedded_connector.helpers import (
    get_data_to_eval_mcode,
    get_data_to_feval_mcode,
    get_mvm_endpoint,
)


def fetch_matlab_proxy_status(url, headers):
    """
    Sends HTTP request to /get_status endpoint of matlab-proxy and returns
    license and MATLAB status.

    Args:
        url (string): Url of matlab-proxy server
        headers (dict): HTTP headers required for communicating with matlab-proxy.

    Returns:
        Tuple (bool, string):
            is_matlab_licensed (bool): True if matlab-proxy has license information, else False.
            matlab_status (string): Status of MATLAB. Values could be "up", "down" and "starting"
            matlab_proxy_has_error (bool): True if matlab-proxy faced any issues and unable to
                                           start MATLAB

    Raises:
        HTTPError: Occurs when connection to matlab-proxy cannot be established.
    """
    resp = requests.get(url + "/get_status", headers=headers, verify=False)
    if resp.status_code == requests.codes.OK:
        data = resp.json()
        is_matlab_licensed = data["licensing"] != None
        matlab_status = data["matlab"]["status"]
        matlab_proxy_has_error = data["error"] != None
        return is_matlab_licensed, matlab_status, matlab_proxy_has_error
    else:
        resp.raise_for_status()


def send_execution_request_to_matlab(url, headers, code):
    """
    Evaluate MATLAB code and capture results.

    Args:
        kernelid (string): A unique kernel identifier.
        url (string): Url of matlab-proxy server
        headers (dict): HTTP headers required for communicating with matlab-proxy
        code (string): MATLAB code to be evaluated

    Returns:
        List(dict): list of outputs captured during evaluation.

    Raises:
        HTTPError: Occurs when connection to matlab-proxy cannot be established.
    """
    return _send_jupyter_request_to_matlab(url, headers, "execute", [code])


def send_completion_request_to_matlab(url, headers, code, cursor_pos):
    """
    Fetch Tab completion results.

    Args:
        url (string): Url of matlab-proxy server
        headers (dict): HTTP headers required for communicating with matlab-proxy
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
    return _send_jupyter_request_to_matlab(url, headers, "complete", [code, cursor_pos])


def send_interrupt_request_to_matlab(url, headers):
    req_body = {
        "messages": {
            "Interrupt": [
                {
                    "uuid": "1234",
                }
            ]
        }
    }
    resp = requests.post(
        get_mvm_endpoint(url),
        headers=headers,
        json=req_body,
        verify=False,
    )
    if resp.status_code != requests.codes.OK:
        resp.raise_for_status()


def _send_feval_request_to_matlab(url, headers, fname, nargout, *args):
    # Add the MATLAB code shipped with kernel to the Path
    path = [str(pathlib.Path(__file__).parent / "matlab")]
    req_body = get_data_to_feval_mcode("addpath", *path, nargout=0)
    original_request = get_data_to_feval_mcode(fname, *args, nargout=nargout)

    # Add the FEval message of original request to the req_body FEval list.
    req_body["messages"]["FEval"].append(original_request["messages"]["FEval"][0])

    # Set the deque mode to make execution synchronous.
    req_body["messages"]["FEval"][0]["dequeMode"] = "non_debug_prompt"
    req_body["messages"]["FEval"][1]["dequeMode"] = "non_debug_prompt"

    resp = requests.post(
        get_mvm_endpoint(url),
        headers=headers,
        json=req_body,
        verify=False,
    )
    if resp.status_code == requests.codes.OK:
        response_data = resp.json()
        try:
            feval_response = response_data["messages"]["FEvalResponse"][1]
        except KeyError:
            # In certain cases when the HTTPResponse is received, it does not
            # contain the expected data. In these cases most likely MATLAB has
            # gone away. Hence we raise the HTTPError to indicate MATLAB is not
            # available.
            raise requests.HTTPError()

        # If the feval request succeeded and outputs are present, return the result.
        if not feval_response["isError"]:
            if nargout != 0 and feval_response["results"]:
                return feval_response["results"][0]

            # Return empty list if there are no outputs in the repsonse
            return []

        # Handle error case. This happens when "Interrupt Kernel" is issued.
        if feval_response["messageFaults"][0]["message"] == "":
            error_message = "Failed to execute. Operation may have interrupted by user."
        else:
            error_message = "Failed to execute. Please try again."
        raise Exception(error_message)
    else:
        raise resp.raise_for_status()


def _send_eval_request_to_matlab(url, headers, mcode):
    # Add the MATLAB code shipped with kernel to the Path
    path = str(pathlib.Path(__file__).parent / "matlab")
    mcode = 'addpath("' + path + '")' + ";" + mcode

    req_body = get_data_to_eval_mcode(mcode)
    resp = requests.post(
        get_mvm_endpoint(url),
        headers=headers,
        json=req_body,
        verify=False,
    )
    if resp.status_code == requests.codes.OK:
        response_data = resp.json()
        try:
            eval_response = response_data["messages"]["EvalResponse"][0]
        except KeyError:
            # In certain cases when the HTTPResponse is received, it does not
            # contain the expected data. In these cases most likely MATLAB has
            # gone away. Hence we raise the HTTPError to indicate MATLAB is not
            # available.
            raise requests.HTTPError()

        # If the eval request succeeded, return the json decoded result.
        if not eval_response["isError"]:
            result_filepath = eval_response["responseStr"].strip()

            # If the filepath in the response is not empty, read the result from
            # file and delete the file.
            if result_filepath != "":
                with open(result_filepath, "r") as f:
                    result = f.read().strip()

                try:
                    import os

                    os.remove(result_filepath)
                except Exception:
                    pass
            else:
                result = ""

            # If result is empty, populate dummy json
            if result == "":
                result = "[]"
            return json.loads(result)

        # Handle the error cases
        if eval_response["messageFaults"]:
            # This happens when "Interrupt Kernel" is issued from a different
            # kernel. There may be other cases also.
            error_message = (
                "Failed to execute. Operation may have been interrupted by user."
            )
        else:
            # This happens when "Interrupt Kernel" is issued from the same kernel.
            # The responseStr contains the error message
            error_message = eval_response["responseStr"].strip()
        raise Exception(error_message)
    else:
        raise resp.raise_for_status()


def _send_jupyter_request_to_matlab(url, headers, request_type, inputs):
    execution_request_type = "feval"

    inputs.insert(0, request_type)
    inputs.insert(1, execution_request_type)

    if execution_request_type == "feval":
        resp = _send_feval_request_to_matlab(
            url, headers, "processJupyterKernelRequest", 1, *inputs
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
            + f"'"
        )
        if request_type == "complete":
            cursor_pos = inputs[3]
            args = args + "," + str(cursor_pos)

        eval_mcode = f"processJupyterKernelRequest({args})"
        resp = _send_eval_request_to_matlab(url, headers, eval_mcode)

    return resp
