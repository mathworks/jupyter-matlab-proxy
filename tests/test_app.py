# Copyright 2021 The MathWorks, Inc.

import pytest, asyncio, aiohttp, json, time
from aiohttp import web
from jupyter_matlab_proxy import app
from jupyter_matlab_proxy.util.mwi_exceptions import MatlabInstallError


def test_create_app():
    """Test if aiohttp server is being created successfully.

    Checks if the aiohttp server is created successfully, routes, startup and cleanup
    tasks are added.
    """
    test_server = app.create_app()

    # Verify router is configured with some routes
    assert test_server.router._resources is not None

    # Verify app server has startup and cleanup tasks
    # By default there is 1 start up and clean up task
    assert len(test_server._on_startup) > 1
    assert len(test_server.on_cleanup) > 1


def get_email():
    """A helper method which returns a placeholder email

    Returns:
        String: A placeholder email as a string.
    """
    return "abc@mathworks.com"


def get_connection_string():
    """A helper method which returns a placeholder nlm connection string

    Returns:
        String : A placeholder nlm connection string
    """
    return "nlm@localhost.com"


@pytest.fixture(
    name="licensing_data",
    params=[
        {"input": None, "expected": None},
        {
            "input": {"type": "mhlm", "email_addr": get_email()},
            "expected": {
                "type": "MHLM",
                "emailAddress": get_email(),
                "entitlements": [],
                "entitlementId": None,
            },
        },
        {
            "input": {"type": "nlm", "conn_str": get_connection_string()},
            "expected": {"type": "NLM", "connectionString": get_connection_string()},
        },
    ],
    ids=[
        "No Licensing info  supplied",
        "Licensing type is MHLM",
        "Licensing type is NLM",
    ],
)
def licensing_info_fixture(request):
    """A pytest fixture which returns licensing_data

    A parameterized pytest fixture which returns a licensing_data dict.
    licensing_data of three types:
        None : No licensing
        MHLM : Matlab Hosted License Manager
        NLM : Network License Manager.


    Args:
        request : A built-in pytest fixture

    Returns:
        Array : Containing expected and actual licensing data.
    """
    return request.param


def test_marshal_licensing_info(licensing_data):
    """Test app.marshal_licensing_info method works correctly

    This test checks if app.marshal_licensing_info returns correct licensing data.
    Test checks for 3 cases:
        1) No Licensing Provided
        2) MHLM type Licensing
        3) NLM type licensing

    Args:
        licensing_data (Array): An array containing actual and expected licensing data to assert.
    """

    actual_licensing_info = licensing_data["input"]
    expected_licensing_info = licensing_data["expected"]

    assert app.marshal_licensing_info(actual_licensing_info) == expected_licensing_info


@pytest.mark.parametrize(
    "actual_error, expected_error",
    [
        (None, None),
        (
            MatlabInstallError("'matlab' executable not found in PATH"),
            {
                "message": "'matlab' executable not found in PATH",
                "logs": None,
                "type": MatlabInstallError.__name__,
            },
        ),
    ],
    ids=["No error", "Raise Matlab Install Error"],
)
def test_marshal_error(actual_error, expected_error):
    """Test if marshal_error returns an expected Dict when an error is raised

    Upon raising MatlabInstallError, checks if the the relevant information is returned as a
    Dict.

    Args:
        actual_error (Exception): An instance of Exception class
        expected_error (Dict): A python Dict containing information on the type of Exception
    """
    assert app.marshal_error(actual_error) == expected_error


class FakeServer:
    """Context Manager class which returns a web server wrapped in aiohttp_client pytest fixture
    for testing.
    """

    def __init__(self, loop, aiohttp_client):
        self.loop = loop
        self.aiohttp_client = aiohttp_client

    def __enter__(self):
        self.server = app.create_app()
        self.runner = web.AppRunner(self.server)
        self.loop.run_until_complete(self.runner.setup())

        self.site = web.TCPSite(
            self.runner,
            host=self.server["settings"]["host_interface"],
            port=self.server["settings"]["app_port"],
        )
        self.loop.run_until_complete(self.site.start())

        return self.loop.run_until_complete(self.aiohttp_client(self.server))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.loop.run_until_complete(self.runner.shutdown())
        self.loop.run_until_complete(self.runner.cleanup())


@pytest.fixture(name="test_server")
def test_server_fixture(
    loop,
    aiohttp_client,
):
    """A pytest fixture which yields a test server to be used by tests.

    Args:
        loop (Event loop): The built-in event loop provided by pytest.
        aiohttp_client (aiohttp_client): Built-in pytest fixture used as a wrapper to the aiohttp web server.

    Yields:
        aiohttp_client : A aiohttp_client server used by tests.
    """

    with FakeServer(loop, aiohttp_client) as test_server:
        yield test_server


async def test_get_status_route(test_server):
    """Test to check endpoint : "/get_status"

    Args:
        test_server (aiohttp_client): A aiohttp_client server for sending GET request.
    """

    resp = await test_server.get("/get_status")
    assert resp.status == 200


async def test_start_matlab_route(test_server):
    """Test to check endpoint : "/start_matlab"

    Test waits for matlab status to be "up" before sending the GET request to start matlab
    Checks whether matlab restarts.

    Args:
        test_server (aiohttp_client): A aiohttp_client server to send GET request to.
    """
    # Waiting for the matlab process to start up.
    max_tries = 5
    count = 0
    while True:
        resp = await test_server.get("/get_status")
        assert resp.status == 200

        resp_json = json.loads(await resp.text())
        if resp_json["matlab"]["status"] == "up":
            break
        else:
            count += 1
            await asyncio.sleep(0.5)
            if count > max_tries:
                raise ConnectionError

    # Send get request to end point
    await test_server.put("/start_matlab")
    resp = await test_server.get("/get_status")
    assert resp.status == 200
    resp_json = json.loads(await resp.text())
    count = 0
    # Check if Matlab restarted successfully
    while True:
        resp = await test_server.get("/get_status")
        assert resp.status == 200
        if resp_json["matlab"]["status"] != "down":
            break
        else:
            count += 1
            await asyncio.sleep(0.5)
            if count > max_tries:
                raise ConnectionError


async def test_stop_matlab_route(test_server):
    """Test to check endpoint : "/stop_matlab"

    Sends HTTP DELETE request to stop matlab and checks if matlab status is down.
    Args:
        test_server (aiohttp_client): A aiohttp_client server to send HTTP DELETE request.
    """
    resp = await test_server.delete("/stop_matlab")
    assert resp.status == 200

    resp_json = json.loads(await resp.text())
    assert resp_json["matlab"]["status"] == "down"


async def test_root_redirect(test_server):
    """Test to check endpoint : "/"

    Should throw a 404 error. This will look for index.html in root directory of the project
    (In non-dev mode, root directory is the package)
    This file will not be available in the expected location in dev mode.

    Args:
        test_server (aiohttp_client):  A aiohttp_client server to send HTTP GET request.

    """
    resp = await test_server.get("/")
    assert resp.status == 404


@pytest.fixture(name="proxy_payload")
def proxy_payload_fixture():
    """Pytest fixture which returns a Dict representing the payload.

    Returns:
        Dict: A Dict representing the payload for HTTP request.
    """
    payload = {"messages": {"ClientType": [{"properties": {"TYPE": "jsd"}}]}}

    return payload


async def test_matlab_proxy_404(proxy_payload, test_server):
    """Test to check if test_server is able to proxy HTTP request to fake matlab server
    for a non-existing file. Should return 404 status code in response

    Args:
        proxy_payload (Dict): Pytest fixture which returns a Dict.
        test_server (aiohttp_client): Test server to send HTTP requests.
    """

    headers = {"content-type": "application/json"}

    # Request a non-existing html file.
    # Request gets proxied to app.matlab_view() which should raise HTTPNotFound() exception ie. return HTTP status code 404
    resp = await test_server.post(
        "./1234.html", data=json.dumps(proxy_payload), headers=headers
    )
    assert resp.status == 404


async def test_matlab_proxy_http_get_request(proxy_payload, test_server):
    """Test to check if test_server proxies a HTTP request to fake matlab server and returns
    the response back

    Args:
        proxy_payload (Dict): Pytest fixture which returns a Dict representing payload for the HTTP request
        test_server (aiohttp_client): Test server to send HTTP requests.

    Raises:
        ConnectionError: If fake matlab server is not reachable from the test server, raises ConnectionError
    """

    max_tries = 5
    count = 0

    while True:
        resp = await test_server.get(
            "/http_get_request.html", data=json.dumps(proxy_payload)
        )

        if resp.status == 404:
            time.sleep(1)
            count += 1

        else:
            resp_body = await resp.text()
            assert json.dumps(proxy_payload) == resp_body
            break

        if count > max_tries:
            raise ConnectionError


async def test_matlab_proxy_http_put_request(proxy_payload, test_server):
    """Test to check if test_server proxies a HTTP request to fake matlab server and returns
    the response back

    Args:
        proxy_payload (Dict): Pytest fixture which returns a Dict representing payload for the HTTP request
        test_server (aiohttp_client): Test server to send HTTP requests.

    Raises:
        ConnectionError: If fake matlab server is not reachable from the test server, raises ConnectionError
    """

    max_tries = 5
    count = 0

    while True:
        resp = await test_server.put(
            "/http_put_request.html", data=json.dumps(proxy_payload)
        )

        if resp.status == 404:
            time.sleep(1)
            count += 1

        else:
            resp_body = await resp.text()
            assert json.dumps(proxy_payload) == resp_body
            break

        if count > max_tries:
            raise ConnectionError


async def test_matlab_proxy_http_delete_request(proxy_payload, test_server):
    """Test to check if test_server proxies a HTTP request to fake matlab server and returns
    the response back

    Args:
        proxy_payload (Dict): Pytest fixture which returns a Dict representing payload for the HTTP request
        test_server (aiohttp_client): Test server to send HTTP requests.

    Raises:
        ConnectionError: If fake matlab server is not reachable from the test server, raises ConnectionError
    """

    max_tries = 5
    count = 0

    while True:
        resp = await test_server.delete(
            "/http_delete_request.html", data=json.dumps(proxy_payload)
        )

        if resp.status == 404:
            time.sleep(1)
            count += 1

        else:
            resp_body = await resp.text()
            assert json.dumps(proxy_payload) == resp_body
            break

        if count > max_tries:
            raise ConnectionError


async def test_matlab_proxy_http_post_request(proxy_payload, test_server):
    """Test to check if test_server proxies http post request to fake matlab server.
    Checks if payload is being modified before proxying.
    Args:
        proxy_payload (Dict): Pytest fixture which returns a Dict representing payload for the HTTP Request
        test_server (aiohttp_client): Test server to send HTTP requests

    Raises:
        ConnectionError: If unable to proxy to fake matlab server raise Connection error
    """
    max_tries = 5
    count = 0

    while True:
        resp = await test_server.post(
            "/http_post_request.html/asdfjkl;/messageservice/json/secure",
            data=json.dumps(proxy_payload),
        )

        if resp.status == 404:
            time.sleep(1)
            count += 1

        else:
            resp_body = await resp.text()
            proxy_payload["messages"]["ClientType"][0]["properties"][
                "TYPE"
            ] = "jsd_rmt_tmw"
            assert json.dumps(proxy_payload) == resp_body
            break

        if count > max_tries:
            raise ConnectionError


async def test_matlab_proxy_web_socket(test_server):
    """Test to check if test_server proxies web socket request to fake matlab server

    Args:
        test_server (aiohttp_client): Test Server to send HTTP Requests.
    """

    headers = {
        "connection": "Upgrade",
        "upgrade": "websocket",
    }

    resp = await test_server.ws_connect("/http_ws_request.html", headers=headers)
    text = await resp.receive()
    assert text.type == aiohttp.WSMsgType.CLOSED


async def test_set_licensing_info_put_nlm(test_server):
    """Test to check endpoint : "/set_licensing_info"

    Test which sends HTTP PUT request with NLM licensing information.
    Args:
        test_server (aiohttp_client): A aiohttp_client server to send HTTP GET request.
    """

    data = {
        "type": "NLM",
        "status": "starting",
        "version": "R2020b",
        "connectionString": "abc@nlm",
    }
    resp = await test_server.put("/set_licensing_info", data=json.dumps(data))
    assert resp.status == 200


async def test_set_licensing_info_put_invalid_license(test_server):
    """Test to check endpoint : "/set_licensing_info"

    Test which sends HTTP PUT request with INVALID licensing information type.
    Args:
        test_server (aiohttp_client): A aiohttp_client server to send HTTP GET request.
    """

    data = {
        "type": "INVALID_TYPE",
        "status": "starting",
        "version": "R2020b",
        "connectionString": "abc@nlm",
    }
    resp = await test_server.put("/set_licensing_info", data=json.dumps(data))
    assert resp.status == 400


async def test_set_licensing_info_put_mhlm(test_server):
    """Test to check endpoint : "/set_licensing_info"

    Test which sends HTTP PUT request with MHLM licensing information.
    Args:
        test_server (aiohttp_client): A aiohttp_client server to send HTTP GET request.
    """

    data = {
        "type": "MHLM",
        "status": "starting",
        "version": "R2020b",
        "token": "abc@nlm",
        "emailaddress": "abc@nlm",
        "sourceId": "abc@nlm",
    }
    resp = await test_server.put("/set_licensing_info", data=json.dumps(data))
    assert resp.status == 200


async def test_set_licensing_info_delete(test_server):
    """Test to check endpoint : "/set_licensing_info"

    Test which sends HTTP DELETE request to remove licensing. Checks if licensing is set to None
    After request is sent.
    Args:
        test_server (aiohttp_client):  A aiohttp_client server to send HTTP GET request.
    """

    resp = await test_server.delete("/set_licensing_info")
    resp_json = json.loads(await resp.text())
    assert resp.status == 200 and resp_json["licensing"] is None


async def test_set_termination_integration_delete(test_server):
    """Test to check endpoint : "/terminate_integration"

    Test which sends HTTP DELETE request to terminate integration. Checks if integration is terminated
    successfully.
    Args:
        test_server (aiohttp_client):  A aiohttp_client server to send HTTP GET request.
    """

    resp = await test_server.delete("/terminate_integration")
    resp_json = json.loads(await resp.text())
    assert resp.status == 200 and resp_json["loadUrl"] == "../"
