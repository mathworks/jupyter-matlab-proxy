# Copyright 2023 The MathWorks, Inc.
"""Mock matlab-proxy HTTP Responses."""

import requests
from requests.exceptions import HTTPError


class MockUnauthorisedRequestResponse:
    """
    Emulates an unauthorized request to matlab-proxy.

    Raises:
        HTTPError: with code unauthorized.
    """

    exception_msg = "Mock exception thrown due to unauthorized request status."
    status_code = requests.codes.unauthorized

    def raise_for_status(self):
        """Raise a HTTPError with unauthorised request message."""
        raise HTTPError(self.exception_msg)


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

    status_code = requests.codes.ok

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

    def json(self):
        """Return a matlab-proxy status JSON object."""
        return {
            "licensing": self.licensed,
            "matlab": {"status": self.matlab_status},
            "error": self.error,
        }


class MockSimpleOkResponse:
    """A mock of a successful http request that returns empty json."""

    status_code = requests.codes.ok

    @staticmethod
    def json():
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

    status_code = requests.codes.bad

    def raise_for_status(self):
        """Raise a HTTPError with custom error message."""
        raise HTTPError(self.error_message)


class MockError(Exception):
    """An example error used for testing purposes

    Args:
        Exception (Any): Dummy exception
    """

    pass
