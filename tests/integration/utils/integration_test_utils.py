# Copyright 2023-2026 The MathWorks, Inc.
# Utility functions for integration testing of jupyter-matlab-proxy

import asyncio
import os
import socket
import time
import requests
from matlab_proxy.settings import get_process_startup_timeout

MATLAB_STARTUP_TIMEOUT = get_process_startup_timeout()


def perform_basic_checks():
    """
    Perform basic checks for the prerequisites for starting
    matlab-proxy
    """
    import matlab_proxy.settings

    # Validate MATLAB before testing
    _, matlab_path = matlab_proxy.settings.get_matlab_executable_and_root_path()

    # Check if MATLAB is in the system path
    assert matlab_path is not None, "MATLAB is not in system path"

    # Check if MATLAB version is >= R2020b
    assert (
        matlab_proxy.settings.get_matlab_version(matlab_path) >= "R2020b"
    ), "MATLAB version should be R2020b or later"


async def wait_matlab_proxy_ready(matlab_proxy_url):
    """
    Wait for matlab-proxy to be up and running

    Args:
        matlab_proxy_url (string): URL to access matlab-proxy
    """

    from jupyter_matlab_kernel.mwi_comm_helpers import MWICommHelper

    start_time = time.time()

    loop = asyncio.get_event_loop()
    comm_helper = MWICommHelper("", matlab_proxy_url, loop, loop, {})
    matlab_proxy_status = await comm_helper.fetch_matlab_proxy_status()

    # Poll for matlab-proxy to be up
    while (
        matlab_proxy_status
        and matlab_proxy_status.matlab_status in ["down", "starting"]
        and (time.time() - start_time < MATLAB_STARTUP_TIMEOUT)
        and not matlab_proxy_status.matlab_proxy_has_error
    ):
        time.sleep(1)
        try:
            matlab_proxy_status = await comm_helper.fetch_matlab_proxy_status()
        except Exception:
            # The network connection can be flaky while the
            # matlab-proxy server is booting. There can also be some
            # intermediate connection errors
            pass
    assert matlab_proxy_status.is_matlab_licensed is True, "MATLAB is not licensed"
    assert (
        matlab_proxy_status.matlab_status == "up"
    ), f"matlab-proxy process did not start successfully\nMATLAB Status is '{matlab_proxy_status.matlab_status}'"


def license_matlab_proxy(matlab_proxy_url):
    """
    Use Playwright UI automation to license matlab-proxy.
    Uses TEST_USERNAME and TEST_PASSWORD from environment variables.

    Args:
        matlab_proxy_url (string): URL to access matlab-proxy
    """
    from playwright.sync_api import expect, sync_playwright

    # These are MathWorks Account credentials to license MATLAB
    # Throws 'KeyError' if the following environment variables are not set
    TEST_USERNAME = os.environ["TEST_USERNAME"]
    TEST_PASSWORD = os.environ["TEST_PASSWORD"]

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(matlab_proxy_url)

            # Find the MHLM licensing windows in matlab-proxy
            mhlm_div = page.locator("#MHLM")
            expect(
                mhlm_div,
                "Wait for MHLM licensing window to appear. This might fail if the MATLAB is already licensed",
            ).to_be_visible(timeout=60000)

            # The login iframe is present within the MHLM Div
            login_iframe = mhlm_div.frame_locator("#loginframe")

            # Fills in the username textbox
            email_text_box = login_iframe.locator("#userId")
            expect(
                email_text_box,
                "Wait for email ID textbox to appear",
            ).to_be_visible(timeout=20000)
            email_text_box.fill(TEST_USERNAME)
            email_text_box.press("Enter")

            # Fills in the password textbox
            password_text_box = login_iframe.locator("#password")
            expect(
                password_text_box, "Wait for password textbox to appear"
            ).to_be_visible(timeout=20000)
            password_text_box.fill(TEST_PASSWORD)
            password_text_box.press("Enter")
            password_text_box.press("Enter")

            # Verifies if licensing is successful by checking the status information
            status_info = page.get_by_text("Status Information")
            expect(
                status_info,
                "Verify if Licensing is successful. This might fail if incorrect credentials are provided",
            ).to_be_visible(timeout=60000)
        except Exception as e:
            # Grab screenshots
            log_dir = "./"
            file_name = "licensing-screenshot-failed.png"
            file_path = os.path.join(log_dir, file_name)
            os.makedirs(log_dir, exist_ok=True)
            page.screenshot(path=file_path)
            print("Exception: %s", str(e))
        finally:
            browser.close()


def unlicense_matlab_proxy(matlab_proxy_url):
    """
    Unlicense matlab-proxy that is licensed using online licensing

    Args:
        matlab_proxy_url (string): URL to access matlab-proxy
    """
    import warnings

    max_retries = 3  # Max retries for unlicensing matlab-proxy
    retries = 0

    while retries < max_retries:
        error = None
        try:
            resp = requests.delete(
                matlab_proxy_url + "/set_licensing_info",
                headers={},
                verify=False,
            )
            if resp.status_code == requests.codes.OK:
                data = resp.json()
                assert data["licensing"] is None, "matlab-proxy licensing is not unset"
                assert (
                    data["matlab"]["status"] == "down"
                ), "matlab-proxy is not in 'stopped' state"

                # Throw warning if matlab-proxy is unlicensed but with some error
                if data["error"] is not None:
                    warnings.warn(
                        f"matlab-proxy is unlicensed but with error: {data['error']}",
                        UserWarning,
                    )
                break
            else:
                resp.raise_for_status()
        except Exception as e:
            error = e
        finally:
            retries += 1

    # If the above code threw error even after maximum retries, then raise error
    if error:
        raise error
