# Copyright 2024 The MathWorks, Inc.
import os
import sys
import time
import logging
import tempfile
from playwright.sync_api import Page, Error, sync_playwright, expect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


FREE_PORT = os.getenv("TEST_JMP_PORT", "8888")
BASE_URL = os.getenv("TEST_JMP_URL", f"127.0.0.1:{FREE_PORT}")
JLAB_URL = f"{BASE_URL}/lab"
DEFAULT_TMP_DIR = os.path.join(tempfile.gettempdir(), "/jupyterlab-logs")
TIMEOUTS = {
    # Time in milliseconds
    "JLAB_UP": 5 * 60 * 1000,
    "MHLM_VISIBLE": 60 * 1000,
    "TEXTBOX_VISIBLE": 5 * 1000,
    "MATLAB_STARTS": 3 * 60 * 1000,
}
POLL_INTERVAL = 1000


def license_with_existing_license(
    headless: bool = True, log_dir: str = DEFAULT_TMP_DIR
):
    """
    Use Playwright UI automation to license MATLAB via matlab-proxy.
    Uses the fact that the MATLAB has a license file available.
    """
    playwright, browser, page = _launch_browser(headless)
    try:
        _assert_jlab_is_up(page)
        matlab_proxy_page = _go_to_matlab_proxy(page)
        matlab_proxy_page.get_by_role("tab", name="Existing License").click()
        matlab_proxy_page.get_by_role("button", name="Start MATLAB").click()
        _assert_matlab_starts(matlab_proxy_page)
    except Exception as e:
        _take_screenshot(page, log_dir, "page-licensing-failed.png")
        _take_screenshot(matlab_proxy_page, log_dir, "licensing-failed.png")
        raise e
    finally:
        _close_resources(playwright, browser)


def license_with_nlm():
    logger.error("This method has not been implemented yet.")
    sys.exit(1)


def license_with_online_licensing(
    headless: bool = True, log_dir: str = DEFAULT_TMP_DIR
):
    """
    Use Playwright UI automation to license MATLAB via matlab-proxy and online
    licensing.
    Uses TEST_USERNAME and TEST_PASSWORD from environment variables.
    """
    TEST_USERNAME = _get_required_env_variable("TEST_USERNAME")
    TEST_PASSWORD = _get_required_env_variable("TEST_PASSWORD")

    playwright, browser, page = _launch_browser(headless)
    try:
        _assert_jlab_is_up(page)
        matlab_proxy_page = _go_to_matlab_proxy(page)
        login_iframe = _wait_for_login_iframe(matlab_proxy_page)
        email_text_box = _fill_in_username(TEST_USERNAME, login_iframe)
        email_text_box.press("Enter")
        password_text_box = _fill_in_password(TEST_PASSWORD, login_iframe)
        password_text_box.press("Enter")
        _assert_matlab_starts(matlab_proxy_page)
    except Exception as e:
        _take_screenshot(page, log_dir, "page-licensing-failed.png")
        _take_screenshot(matlab_proxy_page, log_dir, "licensing-failed.png")
        raise e
    finally:
        _close_resources(playwright, browser)


def _launch_browser(headless: bool = True) -> tuple:
    """Launches the browser and returns the browser and page objects."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    page = browser.new_page()
    return playwright, browser, page


def _close_resources(playwright, browser):
    """Closes the browser and playwright resources properly."""
    browser.close()
    playwright.stop()


def _assert_matlab_starts(matlab_proxy_page):
    """Waits for the MATLAB Proxy toolbar button to appear."""
    matlab_proxy_toolbar = matlab_proxy_page.get_by_role("button", name="Menu")
    expect(matlab_proxy_toolbar).to_be_visible(timeout=TIMEOUTS["MATLAB_STARTS"])


def _wait_for_login_iframe(matlab_proxy_page):
    """Waits for the MHLM/Online Licensing form to appear."""
    mhlm_div = matlab_proxy_page.locator("#MHLM")
    expect(
        mhlm_div,
        "Wait for MHLM licensing window to appear. This might fail if the MATLAB is already licensed",
    ).to_be_visible(timeout=TIMEOUTS["MHLM_VISIBLE"])

    # The login iframe is present within the MHLM Div
    login_iframe = mhlm_div.frame_locator("#loginframe")
    return login_iframe


def _fill_in_username(username, login_iframe):
    """Inputs the provided username string into the MHLM login form."""
    email_text_box = login_iframe.locator("#userId")
    expect(
        email_text_box,
        "Wait for email ID textbox to appear",
    ).to_be_visible(timeout=TIMEOUTS["TEXTBOX_VISIBLE"])
    email_text_box.fill(username)
    return email_text_box


def _fill_in_password(password, login_iframe):
    """Inputs the provided password string into the MHLM login form."""
    password_text_box = login_iframe.locator("#password")
    expect(password_text_box, "Wait for password textbox to appear").to_be_visible(
        timeout=TIMEOUTS["TEXTBOX_VISIBLE"]
    )
    password_text_box.fill(password)
    return password_text_box


def _assert_jlab_is_up(page):
    """Asserts that JupyterLab is up and running."""
    timeout = TIMEOUTS["JLAB_UP"]
    jlab_api_url = f"{BASE_URL}/api"
    isAlive = _poll_website(page, jlab_api_url, timeout)
    assert isAlive, f"JupyterLab has failed to deploy in {timeout} seconds"


def _take_screenshot(page, log_dir, file_name):
    """Takes a screenshot of the current page."""
    file_path = os.path.join(log_dir, file_name)
    os.makedirs(log_dir, exist_ok=True)
    page.screenshot(path=file_path)
    logger.info(f"Screenshot taken: {file_path}")


def _go_to_matlab_proxy(page):
    """Navigates to the MATLAB Proxy page via the JupyterLab Launcher."""
    # Open MATLAB in browser
    page.goto(JLAB_URL)
    matlab_jsd_button_selector = "text=Open MATLAB [↗]"
    matlab_jsd_button = page.wait_for_selector(matlab_jsd_button_selector)
    context = page.context

    # Check if the matlab-proxy button is visible and click it.
    assert matlab_jsd_button.is_visible()
    matlab_jsd_button.click()

    # Return handle to the new tab where matlab-proxy will have opened.
    matlab_jsd_page = context.wait_for_event("page")
    return matlab_jsd_page


def _poll_website(page: Page, url: str, timeout: int) -> bool:
    """Polls a website until it is available or the timeout is reached."""
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            response = page.goto(url)
            if response and response.status == 200:
                return True
        except Error:
            # swallow the errors
            pass
        page.wait_for_timeout(POLL_INTERVAL)
    return False


def _get_required_env_variable(var_name: str) -> str:
    """Retrieve an environment variable or exit with an error."""
    value = os.getenv(var_name)
    if value is None:
        logger.error(f"The environment variable {var_name} must be set.")
        sys.exit(1)
    return value
