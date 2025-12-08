# Copyright 2023-2025 The MathWorks, Inc.
"""Mock matlab-proxy HTTP Responses."""

import http

import aiohttp.client_exceptions


class MockUnauthorisedRequestResponse:
    """
    Emulates an unauthorized request to matlab-proxy.

    Raises:
        HTTPError: with code unauthorized.
    """

    exception_msg = "Mock exception thrown due to unauthorized request status."
    status = http.HTTPStatus.UNAUTHORIZED

    def raise_for_status(self):
        """Raise a HTTPError with unauthorised request message."""
        raise aiohttp.client_exceptions.ClientError(self.exception_msg)


class MockMatlabProxyStatusResponse:
    """A mock of a matlab-proxy status response."""

    def __init__(self, lic_type, matlab_status, has_error) -> None:
        """Construct a mock matlab-proxy status response.

        Args:
            is_licensed (bool): indicates if MATLAB is licensed.
            matlab_status (string): indicates the MATLAB status, i.e. is it "starting", "running" etc.
            has_error (bool): indicates if there is an error with MATLAB
        """
        self.licensed = self.process_license_type(lic_type)
        self.matlab_status = matlab_status
        self.error = MockError("An example error") if has_error else None

    status = http.HTTPStatus.OK

    @staticmethod
    def handle_entitled_mhlm():
        return {
            "type": "mhlm",
            "emailAddress": "test@mathworks.com",
            "entitlements": [
                {
                    "id": "123456",
                    "label": "MATLAB - Staff Use",
                    "license_number": "123456",
                }
            ],
            "entitlementId": "123456",
        }

    @staticmethod
    def handle_unentitled_mhlm():
        return {
            "type": "mhlm",
            "emailAddress": "test@mathworks.com",
            "entitlements": [
                {
                    "id": "123456",
                    "label": "MATLAB - Staff Use",
                    "license_number": "123456",
                }
            ],
            "entitlementId": None,
        }

    @staticmethod
    def handle_nlm():
        return {"type": "nlm", "connectionString": "123@internal"}

    @staticmethod
    def handle_existing_license():
        return {"type": "existing_license"}

    @staticmethod
    def default():
        return None

    def process_license_type(self, lic_type):
        types = {
            "mhlm_entitled": self.handle_entitled_mhlm,
            "mhlm_unentitled": self.handle_unentitled_mhlm,
            "nlm": self.handle_nlm,
            "existing_license": self.handle_existing_license,
        }
        return types.get(lic_type, self.default)()

    async def json(self):
        """Return a matlab-proxy status JSON object."""
        return {
            "licensing": self.licensed,
            "matlab": {"status": self.matlab_status},
            "error": self.error,
        }


class MockSimpleOkResponse:
    """A mock of a successful http request that returns empty json."""

    status = http.HTTPStatus.OK

    @staticmethod
    async def json():
        """Return an empty JSON struct."""
        return {}


class MockSimpleBadResponse:
    """A mock of a bad https request."""

    def __init__(self, error_message: str) -> None:
        """Construct a mock bad http requests.

        Args:
            error_message (str): the mock will raise a HTTPError with this error message.
        """
        self.error_message = error_message

    status = http.HTTPStatus.BAD_REQUEST

    def raise_for_status(self):
        """Raise a HTTPError with custom error message."""
        raise aiohttp.client_exceptions.ClientError(self.error_message)


class MockError(Exception):
    """An example error used for testing purposes

    Args:
        Exception (Any): Dummy exception
    """

    pass


class MockEvalResponse:
    """A mock of a successful eval response from matlab-proxy."""

    def __init__(self, is_error=False, response_str="", message_faults=None):
        """Construct a mock eval response.

        Args:
            is_error (bool): indicates if the eval had an error.
            response_str (str): the response string or file path.
            message_faults (list): list of message faults if any.
        """
        self.is_error = is_error
        self.response_str = response_str
        self.message_faults = message_faults or []

    status = http.HTTPStatus.OK

    async def json(self):
        """Return a matlab-proxy eval JSON response."""
        return {
            "messages": {
                "EvalResponse": [
                    {
                        "isError": self.is_error,
                        "responseStr": self.response_str,
                        "messageFaults": self.message_faults,
                    }
                ]
            }
        }


class MockEvalResponseMissingData:
    """A mock of an eval response missing EvalResponse data."""

    status = http.HTTPStatus.OK

    def raise_for_status(self):
        """Raise a HTTPError for missing data."""
        raise aiohttp.client_exceptions.ClientError("Mock exception")

    @staticmethod
    async def json():
        """Return a matlab-proxy response missing EvalResponse."""
        return {"messages": {}}
