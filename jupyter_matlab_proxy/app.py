# Copyright 2020-2021 The MathWorks, Inc.

import os
import sys
from aiohttp import web
import aiohttp
import asyncio
import json
import signal
from . import settings
from .app_state import AppState
from .util import mwi_logger
from .util.mwi_exceptions import LicensingError
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env
import pkgutil
import mimetypes

mimetypes.add_type("font/woff", ".woff")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/eot", ".eot")
mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("application/json", ".map")
mimetypes.add_type("image/png", ".ico")


# TODO It is bad practice to have global state in aiohttp applications, instead this
# mount point should be read in the application start up function, then if it is not
# an empty string, registering a subapp with the given prefix. In addition, if it is
# possible and does not mess-up the MATLAB iframe base_url detection, register a
# nested subapp (with a name unlikely to cause collisions) containing this API and the
# static serving.


def marshal_licensing_info(licensing_info):
    if licensing_info is None:
        return None

    if licensing_info["type"] == "mhlm":
        return {
            "type": "MHLM",
            "emailAddress": licensing_info["email_addr"],
            "entitlements": licensing_info.get("entitlements", []),
            "entitlementId": licensing_info.get("entitlement_id", None),
        }
    elif licensing_info["type"] == "nlm":
        return {
            "type": "NLM",
            "connectionString": licensing_info["conn_str"],
        }


def marshal_error(error):
    if error is None:
        return None
    return {
        "message": error.message,
        "logs": error.logs,
        "type": error.__class__.__name__,
    }


def create_status_response(app, loadUrl=None):
    state = app["state"]
    return web.json_response(
        {
            "matlab": {
                "status": state.get_matlab_state(),
                "version": state.settings["matlab_version"],
            },
            "licensing": marshal_licensing_info(state.licensing),
            "loadUrl": loadUrl,
            "error": marshal_error(state.error),
            "wsEnv": state.settings["ws_env"],
        }
    )


async def get_status(req):
    return create_status_response(req.app)


async def start_matlab(req):
    state = req.app["state"]

    # Start MATLAB
    await state.start_matlab(restart=True)

    return create_status_response(req.app)


async def stop_matlab(req):
    state = req.app["state"]

    await state.stop_matlab()

    return create_status_response(req.app)


async def set_licensing_info(req):
    state = req.app["state"]

    data = await req.json()
    lic_type = data.get("type")

    try:
        if lic_type == "NLM":
            await state.set_licensing_nlm(data.get("connectionString"))

        elif lic_type == "MHLM":
            await state.set_licensing_mhlm(
                data.get("token"), data.get("emailAddress"), data.get("sourceId")
            )
        else:
            raise Exception('License type must be "NLM" or "MHLM"!')
    except Exception as e:
        raise web.HTTPBadRequest(text="Error with licensing!")

    # Start MATLAB if licensing is complete
    if state.is_licensed() is True and not isinstance(state.error, LicensingError):

        # Start MATLAB
        await state.start_matlab(restart=True)

    return create_status_response(req.app)


async def licensing_info_delete(req):
    state = req.app["state"]

    # Removing license information implies terminating MATLAB
    await state.stop_matlab()

    # Unset licensing information
    state.unset_licensing()

    # Persist licensing information
    state.persist_licensing()

    return create_status_response(req.app)


async def termination_integration_delete(req):
    state = req.app["state"]

    # Send response manually because this has to happen before the application exits
    res = create_status_response(req.app, "../")
    await res.prepare(req)
    await res.write_eof()

    # End termination with 0 exit code to indicate intentional termination
    await req.app.shutdown()
    await req.app.cleanup()

    """When testing with pytest, its not possible to catch sys.exit(0) using the construct 
    'with pytest.raises()', there by causing the test : test_termination_integration_delete() 
    to fail. Inorder to avoid this, adding the below if condition to check to skip sys.exit(0) when testing
    """
    if not mwi_env.is_testing_mode_enabled():
        sys.exit(0)


async def root_redirect(request):
    return aiohttp.web.HTTPFound("./index.html")


async def static_get(req):
    details = req.app["static_route_table"][req.path]
    return web.Response(
        headers=details["headers"],
        status=200,
        body=pkgutil.get_data(details["mod"], details["name"]),
    )


def make_static_route_table(app):
    from pkg_resources import resource_listdir, resource_isdir
    from . import gui
    from .gui import static
    from .gui.static import css
    from .gui.static import js
    from .gui.static import media

    base_url = app["settings"]["base_url"]

    table = {}

    for (mod, parent) in [
        (gui.__name__, ""),
        (gui.static.__name__, "/static"),
        (gui.static.css.__name__, "/static/css"),
        (gui.static.js.__name__, "/static/js"),
        (gui.static.media.__name__, "/static/media"),
    ]:
        for name in resource_listdir(mod, ""):
            if not resource_isdir(mod, name):
                if name != "__init__.py":

                    # Special case for manifest.json
                    if "manifest.json" in name:
                        content_type = "application/manifest+json"
                    else:
                        content_type = mimetypes.guess_type(name)[0]

                    headers = {"content-type": content_type}
                    headers.update(app["settings"]["mwi_custom_http_headers"])

                    table[f"{base_url}{parent}/{name}"] = {
                        "mod": mod,
                        "name": name,
                        "headers": headers,
                    }

    return table


async def matlab_view(req):

    reqH = req.headers.copy()

    state = req.app["state"]
    matlab_port = state.matlab_port
    matlab_protocol = req.app["settings"]["matlab_protocol"]
    mwapikey = req.app["settings"]["mwapikey"]
    matlab_base_url = f"{matlab_protocol}://localhost:{matlab_port}"

    # WebSocket
    if (
        reqH.get("connection") == "Upgrade"
        and reqH.get("upgrade") == "websocket"
        and req.method == "GET"
    ):
        ws_server = web.WebSocketResponse()
        await ws_server.prepare(req)

        async with aiohttp.ClientSession(
            cookies=req.cookies, connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as client_session:

            async with client_session.ws_connect(
                matlab_base_url + req.path_qs,
            ) as ws_client:

                async def wsforward(ws_from, ws_to):
                    async for msg in ws_from:
                        mt = msg.type
                        md = msg.data
                        if mt == aiohttp.WSMsgType.TEXT:
                            await ws_to.send_str(md)
                        elif mt == aiohttp.WSMsgType.BINARY:
                            await ws_to.send_bytes(md)
                        elif mt == aiohttp.WSMsgType.PING:
                            await ws_to.ping()
                        elif mt == aiohttp.WSMsgType.PONG:
                            await ws_to.pong()
                        elif ws_to.closed:
                            await ws_to.close(code=ws_to.close_code, message=msg.extra)
                        else:
                            raise ValueError(f"Unexpected message type: {msg}")

                await asyncio.wait(
                    [wsforward(ws_server, ws_client), wsforward(ws_client, ws_server)],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                return ws_server

    # Standard HTTP Request
    else:
        # Proxy, injecting request header
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False),
        ) as client_session:
            try:
                req_body = await transform_body(req)
                # Set content length in case of modification
                reqH["Content-Length"] = str(len(req_body))
                reqH["x-forwarded-proto"] = "http"

                async with client_session.request(
                    req.method,
                    f"{matlab_base_url}{req.rel_url}",
                    headers={**reqH, **{"mwapikey": mwapikey}},
                    allow_redirects=False,
                    data=req_body,
                ) as res:

                    headers = res.headers.copy()
                    body = await res.read()
                    headers.update(req.app["settings"]["mwi_custom_http_headers"])

                    return web.Response(headers=headers, status=res.status, body=body)
            except Exception:
                raise web.HTTPNotFound()


async def transform_body(req):
    """Transform some requests as required by the MATLAB JavaScript Desktop."""

    body = await req.read()

    # Only attempt to rewrite requests known to need rewriting
    if req.method == "POST" and req.rel_url.path.endswith("messageservice/json/secure"):
        data = json.loads(body)
        # Change messages.ClientType.properties.TYPE if necessary
        try:
            replace = False
            for client_type in data["messages"]["ClientType"]:
                if client_type["properties"]["TYPE"] == "jsd":
                    client_type["properties"]["TYPE"] = "jsd_rmt_tmw"
                    replace = True

            if replace is True:
                body = json.dumps(data)
        except KeyError:
            pass

    return body


async def license_init(app):
    state = app["state"]

    try:
        await state.init_licensing()
    except asyncio.CancelledError:
        pass


async def matlab_starter(app):
    """Upon app startup, start MATLAB if able to do so."""

    state = app["state"]

    try:
        if state.is_licensed() and state.get_matlab_state() == "down":
            await state.start_matlab()
    except asyncio.CancelledError:
        # Ensure MATLAB is terminated
        await state.stop_matlab()


async def start_background_tasks(app):
    await license_init(app)
    await matlab_starter(app)


async def cleanup_background_tasks(app):
    logger = mwi_logger.get()
    state = app["state"]
    tasks = state.tasks
    for task_name, task in tasks.items():
        if not task.cancelled():
            logger.debug(f"Cancelling MWI task: {task_name} : {task} ")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    await state.stop_matlab()


def create_app():

    app = web.Application()

    # Get application settings
    app["settings"] = settings.get(dev=(mwi_env.is_development_mode_enabled()))

    # TODO Validate any settings

    # Initialise application state
    app["state"] = AppState(app["settings"])

    # In development mode, the node development server proxies requests to this
    # development server instead of serving the static files directly
    if not mwi_env.is_development_mode_enabled():
        app["static_route_table"] = make_static_route_table(app)
        for key in app["static_route_table"].keys():
            app.router.add_route("GET", key, static_get)

    base_url = app["settings"]["base_url"]
    app.router.add_route("GET", f"{base_url}/get_status", get_status)
    app.router.add_route("PUT", f"{base_url}/start_matlab", start_matlab)
    app.router.add_route("DELETE", f"{base_url}/stop_matlab", stop_matlab)
    app.router.add_route("PUT", f"{base_url}/set_licensing_info", set_licensing_info)
    app.router.add_route(
        "DELETE", f"{base_url}/set_licensing_info", licensing_info_delete
    )
    app.router.add_route(
        "DELETE", f"{base_url}/terminate_integration", termination_integration_delete
    )
    app.router.add_route("*", f"{base_url}/", root_redirect)
    app.router.add_route("*", f"{base_url}/{{proxyPath:.*}}", matlab_view)

    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)

    return app


def get_supported_termination_signals():
    return [signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM]


def main():

    logger = mwi_logger.get(init=True)

    logger.info("Starting MATLAB proxy-app")
    logger.info(
        f" with base_url: {os.environ[mwi_env.get_env_name_base_url()]} and "
        f"app_port:{os.environ[mwi_env.get_env_name_app_port()]}."
    )
    if os.environ.get(mwi_env.get_env_name_mhlm_context()) is None:
        logger.info(
            f"\n The webdesktop can be accessed on http://localhost:{os.environ[mwi_env.get_env_name_app_port()]}{os.environ[mwi_env.get_env_name_base_url()]}/index.html"
        )

    app = create_app()

    loop = asyncio.get_event_loop()

    # Override default loggers
    web_logger = None if not mwi_env.is_web_logging_enabled() else logger
    runner = web.AppRunner(app, logger=web_logger, access_log=web_logger)

    loop.run_until_complete(runner.setup())
    site = web.TCPSite(
        runner, host=app["settings"]["host_interface"], port=app["settings"]["app_port"]
    )
    loop.run_until_complete(site.start())

    # Register handlers to trap termination signals
    for signal in get_supported_termination_signals():
        logger.info(f"Installing handler for signal: {signal} ")
        loop.add_signal_handler(signal, lambda: loop.stop())

    loop.run_forever()

    async def shutdown():
        logger.info("Shutting down MATLAB proxy-app")
        for task in asyncio.Task.all_tasks():
            logger.debug(f"calling cancel on all_tasks: {task}")
            task.cancel()
        await app.shutdown()
        await app.cleanup()

        asyncio.ensure_future(exit())

    try:
        loop.run_until_complete(shutdown())
    except:
        pass

    logger.info(
        "Finished shutting down. Thank you for using the MATLAB web desktop proxy."
    )
    loop.close()
    sys.exit(0)
