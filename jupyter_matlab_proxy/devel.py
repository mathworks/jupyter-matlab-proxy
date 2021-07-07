# Copyright 2020-2021 The MathWorks, Inc.

# Development specific functions
import asyncio, aiohttp
from aiohttp import web
import socket, time, os, sys
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env

desktop_html = b"""
<h1>Fake MATLAB Web Desktop</h1>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nulla elit, pharetra id purus vel, euismod posuere magna. Curabitur varius sem id felis tristique pretium. Morbi eu viverra augue. Sed finibus felis eu odio rhoncus egestas. Nulla facilisi. Proin ac pulvinar dolor. Nullam nec posuere massa, sed ullamcorper dolor.</p>
<p>Phasellus posuere lacus at facilisis ullamcorper. Duis placerat risus eget pretium imperdiet. Cras ut nibh non tellus tincidunt commodo. Maecenas quis sem gravida, tempor turpis at, ultrices dui. Mauris porttitor massa erat, sed rutrum ligula convallis eget. Pellentesque posuere vulputate augue, non consectetur ante ultricies non. Proin molestie vitae massa non consectetur. Aliquam a pharetra urna. Praesent suscipit condimentum leo, ac tincidunt elit tincidunt a. Phasellus dignissim lectus eget pulvinar pretium. Vivamus placerat massa eget ligula eleifend mollis. Suspendisse potenti.</p>
<p>Donec egestas blandit fermentum. Nam scelerisque ipsum pharetra nunc condimentum facilisis. Nunc scelerisque dignissim gravida. In facilisis nisl justo, ac euismod turpis porta in. Mauris a tortor velit. Ut in dui ante. Donec leo dolor, fringilla venenatis facilisis in, imperdiet ac ex. Curabitur eget vehicula nisl, sed suscipit diam. Proin elementum justo in lacus ullamcorper, vel fermentum odio fermentum. Etiam tincidunt neque elit, sit amet aliquet nunc vestibulum eu. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae;</p>
<p>Vivamus hendrerit urna turpis, non bibendum dolor accumsan sit amet. Vestibulum suscipit volutpat massa blandit venenatis. Ut ac magna eget nibh vulputate ullamcorper. Curabitur leo mauris, luctus at bibendum eu, dapibus ut erat. Sed sit amet ipsum ac dui pretium rutrum in et libero. Curabitur vel eleifend magna. Ut interdum, orci at lacinia accumsan, purus lacus posuere nibh, eget hendrerit ligula ligula dignissim est. Pellentesque auctor nunc tortor, vel ultrices sem imperdiet at. Sed est quam, varius gravida imperdiet et, interdum et arcu. Nulla sit amet fringilla justo. Phasellus commodo vitae quam vel mollis. Mauris facilisis orci in posuere imperdiet. Morbi non metus sem. Sed feugiat tincidunt erat, nec pellentesque arcu tempus vel. Vestibulum eu mattis est. Vivamus posuere ante non mi laoreet sollicitudin.</p>
<p>Mauris ac nisl libero. Etiam non dui eu est lacinia varius sed a turpis. Nullam et rhoncus augue. Praesent luctus, sapien tempus faucibus eleifend, massa augue tempus nibh, eget placerat eros velit non nunc. Mauris id elementum ligula, a iaculis tellus. Fusce eget volutpat erat. Proin mollis eleifend lorem, vitae tempor dui porttitor ut. Interdum et malesuada fames ac ante ipsum primis in faucibus. In at libero ultrices, fringilla leo et, elementum sapien. Cras at magna pulvinar, congue risus sit amet, gravida nunc. Duis facilisis ex urna, nec aliquet nulla lobortis et. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum semper, justo in tempor tincidunt, sapien lectus laoreet purus, at fermentum ipsum orci in ex. Aenean a diam sit amet sapien efficitur pulvinar. Ut faucibus neque et erat porttitor dictum.</p>
<p>Fusce non feugiat quam. Etiam dapibus mauris nibh, vitae tempor metus ornare ac. Curabitur rutrum, justo ut tincidunt pharetra, eros magna lobortis dui, pellentesque ornare eros quam congue justo. Nulla vulputate, ante nec commodo malesuada, arcu dolor elementum eros, et congue mi lorem id ipsum. Sed scelerisque lorem est, eleifend efficitur dolor mollis in. Aliquam porta ante vitae vehicula imperdiet. Pellentesque varius quam nisi, varius ultricies felis molestie eu. Aliquam tempus est eget dui elementum condimentum. Fusce dapibus sem ac purus lacinia consequat. Mauris varius iaculis egestas. Nunc in sem suscipit, vulputate felis et, commodo sem.</p>
<p>Maecenas ac velit in enim iaculis interdum et in quam. Proin eu molestie justo. In quis nisl sit amet quam consequat elementum. Donec feugiat eros in malesuada consectetur. Etiam condimentum lacinia lectus et vehicula. Aenean dictum ipsum ligula, id molestie velit porttitor ac. Fusce bibendum eros non elit porta egestas. Ut consequat dolor sem, nec tristique neque posuere quis.</p>
<p>Nulla tempor interdum turpis, vel lacinia lectus imperdiet cursus. Maecenas rutrum felis sed tortor pulvinar, sed consectetur est eleifend. Pellentesque eget eros nec nisi euismod suscipit. Aenean sed cursus odio. Pellentesque semper id nisl et tempor. Donec nec lorem ante. Etiam tristique efficitur tincidunt. Sed rhoncus, metus sed pretium pretium, magna purus accumsan augue, sed consectetur erat erat nec ante. Etiam placerat eget urna vel sodales. Vestibulum semper nisi at neque feugiat blandit. Duis tristique elementum erat id viverra. Morbi dapibus accumsan imperdiet. Nam luctus nisi dapibus nibh efficitur elementum. Pellentesque ornare posuere leo. Fusce auctor hendrerit nisi, quis gravida lacus condimentum non.</p>
<p>Vivamus a interdum elit. Sed congue libero sit amet leo tempor, ut vehicula nibh finibus. Cras malesuada ornare urna, ultricies accumsan nulla lobortis a. Suspendisse in nulla eu eros ornare semper. Nullam commodo lobortis sollicitudin. Mauris tincidunt at metus non suscipit. Proin condimentum purus sed eros ornare molestie. Curabitur turpis arcu, pharetra vel luctus sit amet, sollicitudin ut metus. Cras in porta sapien. Ut sed lacinia lacus. Vivamus tristique quam massa, non lobortis enim viverra sed. Nulla vulputate sapien ut ex eleifend pellentesque. Maecenas auctor maximus orci sed iaculis. Etiam eu imperdiet nulla. Aliquam eu nunc nulla. Vestibulum cursus ultrices sapien eget vehicula.</p>
<p>Nam consectetur, felis tristique vulputate mollis, ligula orci malesuada nunc, quis varius tortor mi at urna. Donec finibus elementum turpis, lobortis rhoncus mauris ultrices ac. Vestibulum eget sagittis turpis. Etiam et ipsum est. Mauris efficitur maximus libero. Maecenas laoreet diam vitae facilisis aliquet. Aenean convallis gravida risus, at volutpat felis volutpat et. Aenean sed vehicula nisl. Ut varius mauris at leo porttitor, nec lacinia erat porta. Suspendisse mauris nisl, aliquet sed nibh sit amet, auctor eleifend metus. Vivamus dignissim finibus enim quis hendrerit. Nunc nulla justo, venenatis in malesuada a, porttitor et enim. Nam a faucibus nulla. Proin at pellentesque orci. Duis at ante iaculis, convallis erat a, porta augue.</p>
"""


def wait_for_port(port):
    """Waits for the given port to become available"""

    while True:
        print(f"Waiting for port {port} to be available")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", port))
        except OSError:
            time.sleep(5)
            continue
        # Once successful, close the port and stop waiting
        s.close()
        break


async def web_handler(request):
    return web.Response(content_type="text/html", body=desktop_html)


async def get_request_handler(request):
    return web.Response(text=await request.text())


async def post_request_handler(request):
    return web.Response(text=await request.text())


async def put_request_handler(request):
    return web.Response(text=await request.text())


async def delete_request_handler(request):
    return web.Response(text=await request.text())


async def web_socket_handler(request):
    print("reaching websocket handler")
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    await ws.send_str("Hello world")


async def fake_matlab_started(app):
    """After the specified delay in seconds, create the ready_file unless it should
    error."""

    # If "123@brokenhost" is specified as the MLM_LICENSE_FILE, exit to simulate an
    # error
    nlm = os.environ.get(mwi_env.get_env_name_network_license_manager())
    if nlm == "123@brokenhost":
        # TODO This should output the exact same text as MATLAB would in the same error
        # state
        print("License checkout failed", file=sys.stderr)
        print("Invalid NLM Connection String", file=sys.stderr)
        print("Diagnostic Information", file=sys.stderr)
        sys.exit(1)

    ready_file = app["ready_file"]
    ready_delay = app["ready_delay"]
    try:
        await asyncio.sleep(ready_delay)
        print(f"Creating fake MATLAB Embedded Connector ready file at {ready_file}")
        ready_file.touch()
    except asyncio.CancelledError:
        pass


async def start_background_tasks(app):
    app["ready_file_writer"] = asyncio.create_task(fake_matlab_started(app))


async def cleanup_background_tasks(app):
    app["ready_file_writer"].cancel()
    await app["ready_file_writer"]


def matlab(args):
    port = int(os.environ["MW_CONNECTOR_SECURE_PORT"])
    wait_for_port(port)
    print(f"Serving fake MATLAB Embedded Connector at port {port}")
    app = web.Application()
    app["ready_file"] = args.ready_file
    app["ready_delay"] = args.ready_delay

    app.router.add_route("GET", "/index-jsd-cr.html", web_handler)

    app.router.add_route("GET", "/http_get_request.html", get_request_handler)

    app.router.add_route(
        "POST",
        "/http_post_request.html/{variable}/messageservice/json/secure",
        post_request_handler,
    )

    app.router.add_route("PUT", "/http_put_request.html", put_request_handler)

    app.router.add_route("DELETE", "/http_delete_request.html", delete_request_handler)

    app.router.add_route("GET", "/http_ws_request.html/", web_socket_handler)

    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app, port=port)


if __name__ == "__main__":
    import argparse
    import tempfile
    from pathlib import Path

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    matlab_parser = subparsers.add_parser("matlab")
    matlab_parser.add_argument(
        "--ready-file",
        default=Path(tempfile.gettempdir()) / "connector.securePort",
        type=Path,
    )
    matlab_parser.add_argument("--ready-delay", default=10, type=int)
    matlab_parser.set_defaults(func=matlab)
    args = parser.parse_args()
    args.func(args)
