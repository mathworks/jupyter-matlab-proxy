# Copyright 2020 The MathWorks, Inc.

import xml.etree.ElementTree as ET
import aiohttp
from .exceptions import (
    OnlineLicensingError,
    EntitlementError,
    NetworkLicensingError,
    MatlabError,
)


LICENSING_URL = "https://github.com/mathworks/jupyter-matlab-proxy/blob/main/MATLAB_Licensing_Info.md"


async def fetch_entitlements(mhlm_api_endpoint, access_token, matlab_release):

    # Get entitlements for token
    async with aiohttp.ClientSession() as client_session:
        async with client_session.post(
            f"{mhlm_api_endpoint}?token={access_token}&release={matlab_release}&coreProduct=ML&context=jupyter&excludeExpired=true",
            headers={"content-type": "application/x-www-form-urlencoded"},
        ) as res:

            if res.reason != "OK":
                raise OnlineLicensingError(
                    f"Communication with {mhlm_api_endpoint} failed ({res.status}). For more details, see {LICENSING_URL}."
                )

            root = ET.fromstring(await res.text())
            entitlement_el = root.find("entitlements")

            if entitlement_el is None or len(entitlement_el) == 0:
                raise EntitlementError(
                    f"Your MathWorks account is not linked to a valid license for MATLAB {matlab_release}."
                )

            entitlements = entitlement_el.findall("entitlement")

            return [
                {
                    "id": entitlement.find("id").text,
                    "label": entitlement.find("label").text,
                    "license_number": entitlement.find("license_number").text,
                }
                for entitlement in entitlements
            ]


async def fetch_expand_token(mwa_api_endpoint, identity_token, source_id):

    async with aiohttp.ClientSession() as client_session:
        async with client_session.post(
            f"{mwa_api_endpoint}/tokens?tokenString={identity_token}&tokenPolicyName=R1&sourceId={source_id}",
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "accept": "application/json",
                "X_MW_WS_callerId": "desktop-jupyter",
            },
        ) as res:

            if res.reason != "OK":
                raise OnlineLicensingError(
                    f"Communication with {mwa_api_endpoint} failed ({res.status}). For more details, see {LICENSING_URL}."
                )

            data = await res.json()

            return {
                "expiry": data["expirationDate"],
                "first_name": data["referenceDetail"]["firstName"],
                "last_name": data["referenceDetail"]["lastName"],
                "display_name": data["referenceDetail"]["displayName"],
                "user_id": data["referenceDetail"]["userId"],
                "profile_id": data["referenceDetail"]["referenceId"],
            }


async def fetch_access_token(mwa_api_endpoint, identity_token, source_id):

    async with aiohttp.ClientSession() as client_session:
        async with client_session.post(
            f"{mwa_api_endpoint}/tokens/access?tokenString={identity_token}&type=MWAS&sourceId={source_id}",
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "accept": "application/json",
                "X_MW_WS_callerId": "desktop-jupyter",
            },
        ) as res:

            if res.reason != "OK":
                raise OnlineLicensingError(
                    f"Communication with {mwa_api_endpoint} failed ({res.status}). For more details, see {LICENSING_URL}."
                )

            data = await res.json()

            return {
                "token": data["accessTokenString"],
            }


def range_matlab_connector_ports():
    """ Generator of acceptable ports for MATLAB Connector.

    Allowed ports conform to the regex: [3,6]1[5-9][1-9][1-9]
    """

    for p1 in (3, 6):
        p2 = 1
        for p3 in range(5, 10):
            for p4 in range(1, 10):
                for p5 in range(1, 10):
                    yield int(f"{p1}{p2}{p3}{p4}{p5}")


def parse_nlm_error(logs, conn_str):
    nlm_logs = []
    start = False
    for log in logs:
        if start is False:
            if "License checkout failed" in log:
                start = True
                nlm_logs.append(log)
        else:
            if "Diagnostic Information" in log:
                return NetworkLicensingError(
                    f"License checkout from {conn_str} failed. For more details, see {LICENSING_URL}.",
                    logs=nlm_logs,
                )
            nlm_logs.append(log)
    return None


def parse_mhlm_error(logs):
    mhlm_logs = None
    start = False
    for log in logs:
        if "License Manager Error" in log:
            start = True
            mhlm_logs = [log]

        if start is True:
            mhlm_logs.append(log)

    if mhlm_logs is not None:
        return OnlineLicensingError(
            f"Usage of MathWorks Online Licensing failed. For more details, see {LICENSING_URL}.",
            logs=mhlm_logs,
        )
    return None


def parse_other_error(logs):
    return MatlabError(
        "MATLAB returned an unexpected error. For more details, see the log below.",
        logs=logs
    )
