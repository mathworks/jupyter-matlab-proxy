# Copyright 2023-2026 The MathWorks, Inc.

import asyncio
import uuid

import requests
import matlab_proxy_manager.lib.api as mpm_lib

from tests.integration.utils import integration_test_utils as utils


async def _run_licensing_flow():
    """
    Async coroutine that starts matlab-proxy, licenses it via Playwright,
    waits for it to be ready, and shuts it down.
    """
    caller_id = str(uuid.uuid4())
    parent_id = str(uuid.uuid4())
    utils.perform_basic_checks()

    matlab_proxy_info = await mpm_lib.start_matlab_proxy_for_kernel(
        caller_id, parent_id, is_shared_matlab=True
    )
    mpm_auth_token = matlab_proxy_info.get("mpm_auth_token")

    try:
        headers = matlab_proxy_info.get("headers")
        mwi_auth_token = headers.get("MWI-AUTH-TOKEN")
        matlab_proxy_url = build_url(
            matlab_proxy_info.get("absolute_url"),
            {"mwi-auth-token": mwi_auth_token},
        )

        # License matlab-proxy using playwright UI automation.
        await asyncio.to_thread(utils.license_matlab_proxy, matlab_proxy_url)

        # Wait for matlab-proxy to be up and running
        await utils.wait_matlab_proxy_ready(matlab_proxy_info.get("absolute_url"))
    finally:
        await mpm_lib.shutdown(parent_id, caller_id, mpm_auth_token)


def license_matlab_proxy_mpm():
    """
    Licenses matlab-proxy once by driving the MHLM flow end-to-end:
    starts a matlab-proxy instance, logs in via Playwright, waits for
    it to come up, and shuts it down.
    """
    try:
        asyncio.run(_run_licensing_flow())
    except Exception as err:
        print(f"An error occurred: {err}")
        raise


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
