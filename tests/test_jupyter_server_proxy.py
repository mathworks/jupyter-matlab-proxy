# Copyright 2020 The MathWorks, Inc.

import jupyter_matlab_proxy


def test_get_env():
    port = 10000
    base_url = "/foo/"
    r = jupyter_matlab_proxy._get_env(port, base_url)
    assert r["APP_PORT"] == str(port)
    assert r["BASE_URL"] == f"{base_url}matlab"
