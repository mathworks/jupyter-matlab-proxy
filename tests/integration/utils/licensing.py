# Copyright 2023-2024 The MathWorks, Inc.

import asyncio
import os
from tests.integration.utils import integration_test_utils as utils
import requests
import matlab_proxy_manager.lib.api as mpm_lib
from matlab_proxy import settings as mwi_settings

_MATLAB_STARTUP_TIMEOUT = mwi_settings.get_process_startup_timeout()


def start_matlab_proxy_sync(parent_id, caller_id, isolated_matlab=False):
    """
    Synchronous wrapper to start the MATLAB proxy using asyncio.

    Returns:
        dict: Information about the started MATLAB proxy.
    """
    loop = asyncio.get_event_loop()
    return (
        loop.run_until_complete(
            mpm_lib.start_matlab_proxy_for_kernel(caller_id, parent_id, isolated_matlab)
        ),
        loop,
    )


def shutdown_matlab_proxy_sync(parent_id, caller_id, mpm_auth_token):
    """
    Synchronous wrapper to shut down the MATLAB proxy using asyncio.

    Args:
        mpm_auth_token (str): Authentication token for shutting down the MATLAB proxy.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(mpm_lib.shutdown(parent_id, caller_id, mpm_auth_token))


def start_and_license_matlab_proxy_using_jsp():
    try:
        import matlab_proxy.util

        utils.perform_basic_checks()

        # Select a random free port to serve matlab-proxy for testing
        mwi_app_port = utils.get_random_free_port()
        mwi_base_url = "/matlab-test"

        # '127.0.0.1' is used instead 'localhost' for testing since Windows machines consume
        # some time to resolve 'localhost' hostname
        matlab_proxy_url = f"http://127.0.0.1:{mwi_app_port}{mwi_base_url}"

        # Set the log path based on the test's execution environment
        log_path = "tests/integration/integ_logs.log"
        base_path = os.environ.get(
            "GITHUB_WORKSPACE", os.path.dirname(os.path.abspath(__name__))
        )
        matlab_proxy_logs_path = os.path.join(base_path, log_path)

        # Start matlab-proxy-app for testing
        input_env = {
            # MWI_JUPYTER_TEST env variable is used in jupyter_matlab_kernel/kernel.py
            # to bypass jupyter server for testing
            "MWI_JUPYTER_TEST": "true",
            "MWI_APP_PORT": mwi_app_port,
            "MWI_BASE_URL": mwi_base_url,
            "MWI_LOG_FILE": str(matlab_proxy_logs_path),
            "MWI_ENABLE_TOKEN_AUTH": "false",
        }

        # Get event loop to start matlab-proxy in background
        loop = matlab_proxy.util.get_event_loop()

        # Run matlab-proxy in the background in an event loop
        proc = loop.run_until_complete(
            utils.start_matlab_proxy_app(input_env=input_env)
        )
        # Poll for matlab-proxy URL to respond
        utils.poll_web_service(
            matlab_proxy_url,
            step=5,
            timeout=_MATLAB_STARTUP_TIMEOUT,
            ignore_exceptions=(
                requests.exceptions.ConnectionError,
                requests.exceptions.SSLError,
            ),
        )
        # License matlab-proxy using playwright UI automation
        utils.license_matlab_proxy(matlab_proxy_url)

        # Wait for matlab-proxy to be up and running
        loop.run_until_complete(utils.wait_matlab_proxy_ready(matlab_proxy_url))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        try:
            shutdown_matlab_proxy_jsp(matlab_proxy_url, proc)

        except Exception as e:
            print(f"Failed to shut down matlab-proxy: {e}")


def shutdown_matlab_proxy_jsp(url, proc):
    # Request timeouts
    timeout = 120  # seconds
    # Send shutdown_integration request to MATLAB Proxy
    shutdown_url = f"{url}/shutdown_integration"
    try:
        requests.delete(shutdown_url, timeout=timeout)
    except requests.exceptions.Timeout:
        print("Timed out waiting for matlab-proxy to shutdown, killing process.")
        proc.kill()


def license_matlab_proxy_mpm():
    import time

    """
    Pytest fixture for managing a standalone matlab-proxy process
    for testing purposes. This fixture sets up a matlab-proxy process in
    the module scope, and tears it down after all the tests are executed.

    Args:
        monkeypatch_module_scope (fixture): returns a MonkeyPatch object
        available in module scope
    """

    try:
        import uuid

        caller_id = str(uuid.uuid4())
        parent_id = str(uuid.uuid4())
        utils.perform_basic_checks()

        matlab_proxy_info, loop = start_matlab_proxy_sync(parent_id, caller_id)
        headers = matlab_proxy_info.get("headers")
        mwi_auth_token = headers.get("MWI-AUTH-TOKEN")
        matlab_proxy_url = build_url(
            matlab_proxy_info.get("absolute_url"),
            {"mwi-auth-token": mwi_auth_token},
        )
        mpm_auth_token = matlab_proxy_info.get("mpm_auth_token")

        # License matlab-proxy using playwright UI automation
        utils.license_matlab_proxy(matlab_proxy_url)

        # Wait for matlab-proxy to be up and running
        loop.run_until_complete(
            utils.wait_matlab_proxy_ready(matlab_proxy_info.get("absolute_url"))
        )

    except Exception as err:
        print(f"An error occurred: {err}")
    finally:
        try:
            shutdown_matlab_proxy_sync(parent_id, caller_id, mpm_auth_token)

        except Exception as e:
            print(f"Failed to shut down matlab-proxy: {e}")


def build_url(url, query_params):
    """
    Constructs a full URL with the given base URL, path, and query parameters.

    Args:
        url (str): The base URL (e.g., "https://example.com").
        query_params (dict): A dictionary of query parameters (e.g., {"key1": "value1", "key2": "value2"}).

    Returns:
        str: The full URL with encoded query parameters.
    """

    return requests.Request("GET", url, params=query_params).prepare().url
