# Copyright 2020-2021 The MathWorks, Inc.

import asyncio
from jupyter_matlab_proxy import mwi_environment_variables as mwi_env
import xml.etree.ElementTree as ET
import os
import json
import pty
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import socket
import errno
from collections import deque
from .util import mw, mwi_logger, mwi_validators
from .util.mwi_exceptions import (
    LicensingError,
    InternalError,
    OnlineLicensingError,
    EntitlementError,
    MatlabInstallError,
    NetworkLicensingError,
    log_error,
)


logger = mwi_logger.get()


class AppState:
    def __init__(self, settings):
        self.settings = settings
        self.processes = {"matlab": None, "xvfb": None}
        self.matlab_port = None
        self.licensing = None
        self.tasks = {}
        self.logs = {
            "matlab": deque(maxlen=200),
        }
        self.error = None

        # Start in an error state if MATLAB is not present
        if not self.is_matlab_present():
            self.error = MatlabInstallError("'matlab' executable not found in PATH")
            logger.error("'matlab' executable not found in PATH")
            return

    def __get_cached_licensing_file(self):
        """Get the cached licensing file

        Returns:
            Path : Path object to cached licensing file
        """
        return self.settings["matlab_config_file"]

    def __delete_cached_licensing_file(self):
        try:
            logger.info(f"Deleting any cached licensing files!")
            os.remove(self.__get_cached_licensing_file())
        except FileNotFoundError:
            # The file being absent is acceptable.
            pass

    def __reset_and_delete_cached_licensing(self):
        logger.info(f"Resetting cached licensing information...")
        self.licensing = None
        self.__delete_cached_licensing_file()

    async def __update_and_persist_licensing(self):
        successful_update = await self.update_entitlements()
        if successful_update:
            self.persist_licensing()
        else:
            self.__reset_and_delete_cached_licensing()
        return successful_update

    async def init_licensing(self):
        """Initialize licensing from environment variable or cached file.

        Greater precedence is given to value specified in environment variable MLM_LICENSE_FILE
            If specified, this function will delete previously cached licensing information.
            This enforces a clear understanding of what was used to initialize licensing.
            The contents of the environment variable are NEVER cached.
        """

        # Default value
        self.licensing = None

        # NLM Connection String set in environment
        if self.settings["nlm_conn_str"] is not None:
            nlm_licensing_str = self.settings["nlm_conn_str"]
            logger.info(f"Found NLM:[{nlm_licensing_str}] set in environment")
            logger.info(f"Using NLM string to connect ... ")
            self.licensing = {
                "type": "nlm",
                "conn_str": nlm_licensing_str,
            }
            self.__delete_cached_licensing_file()

        # If NLM connection string is not present, then look for persistent LNU info
        elif self.__get_cached_licensing_file().exists():
            with open(self.__get_cached_licensing_file(), "r") as f:
                licensing = json.loads(f.read())
                logger.info("Found cached licensing information...")
                try:
                    if licensing["type"] == "nlm":
                        # Note: Only NLM settings entered in browser were cached.
                        self.licensing = {
                            "type": "nlm",
                            "conn_str": licensing["conn_str"],
                        }
                    elif licensing["type"] == "mhlm":
                        self.licensing = {
                            "type": "mhlm",
                            "identity_token": licensing["identity_token"],
                            "source_id": licensing["source_id"],
                            "expiry": licensing["expiry"],
                            "email_addr": licensing["email_addr"],
                            "first_name": licensing["first_name"],
                            "last_name": licensing["last_name"],
                            "display_name": licensing["display_name"],
                            "user_id": licensing["user_id"],
                            "profile_id": licensing["profile_id"],
                            "entitlements": [],
                            "entitlement_id": licensing.get("entitlement_id"),
                        }

                        expiry_window = datetime.strptime(
                            self.licensing["expiry"], "%Y-%m-%dT%H:%M:%S.%f%z"
                        ) - timedelta(hours=1)

                        if expiry_window > datetime.now(timezone.utc):
                            successful_update = (
                                await self.__update_and_persist_licensing()
                            )
                            if successful_update:
                                logger.info("Successful re-use of cached information.")
                        else:
                            self.__reset_and_delete_cached_licensing()
                    else:
                        # Somethings wrong, licensing is neither NLM or MHLM
                        self.__reset_and_delete_cached_licensing()
                except Exception as e:
                    self.__reset_and_delete_cached_licensing()

    def get_matlab_state(self):
        """Determine the state of MATLAB to be down/starting/up."""

        matlab = self.processes["matlab"]
        xvfb = self.processes["xvfb"]

        # MATLAB process never started
        if matlab is None:
            return "down"
        # MATLAB process previously started, but not running
        elif matlab.returncode is not None:
            return "down"
        # Xvfb never started
        elif xvfb is None:
            return "down"
        # Xvfb process previously started, but not running
        elif xvfb.returncode is not None:
            return "down"
        # MATLAB processes started and MATLAB Embedded Connector ready file present
        elif self.settings["matlab_ready_file"].exists():
            return "up"
        # MATLAB processes started, but MATLAB Embedded Connector not ready
        return "starting"

    async def set_licensing_nlm(self, conn_str):
        """Set the licensing type to NLM and the connection string."""

        # TODO Validate connection string
        self.licensing = {"type": "nlm", "conn_str": conn_str}
        self.persist_licensing()

    async def set_licensing_mhlm(
        self,
        identity_token,
        email_addr,
        source_id,
        entitlements=[],
        entitlement_id=None,
    ):
        """Set the licensing type to MHLM and the details."""

        try:

            token_data = await mw.fetch_expand_token(
                self.settings["mwa_api_endpoint"], identity_token, source_id
            )

            self.licensing = {
                "type": "mhlm",
                "identity_token": identity_token,
                "source_id": source_id,
                "expiry": token_data["expiry"],
                "email_addr": email_addr,
                "first_name": token_data["first_name"],
                "last_name": token_data["last_name"],
                "display_name": token_data["display_name"],
                "user_id": token_data["user_id"],
                "profile_id": token_data["profile_id"],
                "entitlements": entitlements,
                "entitlement_id": entitlement_id,
            }

            successful_update = await self.__update_and_persist_licensing()
            if successful_update:
                logger.info("Login successful, persisting login information.")

        except OnlineLicensingError as e:
            self.error = e
            self.licensing = {
                "type": "mhlm",
                "email_addr": email_addr,
            }
            log_error(logger, e)

    def unset_licensing(self):
        """Unset the licensing."""

        self.licensing = None

        # If the error was due to licensing, clear it
        if isinstance(self.error, LicensingError):
            self.error = None

    def is_licensed(self):
        """Is MATLAB licensing configured?"""

        if self.licensing is not None:
            if self.licensing["type"] == "nlm":
                if self.licensing["conn_str"] is not None:
                    return True
            elif self.licensing["type"] == "mhlm":
                if (
                    self.licensing.get("identity_token") is not None
                    and self.licensing.get("source_id") is not None
                    and self.licensing.get("expiry") is not None
                    and self.licensing.get("entitlement_id") is not None
                ):
                    return True
        return False

    def is_matlab_present(self):
        """Is MATLAB install accessible?"""

        return self.settings["matlab_path"] is not None

    async def update_entitlements(self):
        """Speaks to MW and updates MHLM entitlements

        Returns: True if update was successful
        Raises:
            InternalError: OnlineLicensingError, EntitlementError
        """
        if self.licensing is None or self.licensing["type"] != "mhlm":
            raise InternalError(
                "MHLM licensing must be configured to update entitlements!"
            )

        try:
            # Fetch an access token
            access_token_data = await mw.fetch_access_token(
                self.settings["mwa_api_endpoint"],
                self.licensing["identity_token"],
                self.licensing["source_id"],
            )

            # Fetch entitlements
            entitlements = await mw.fetch_entitlements(
                self.settings["mhlm_api_endpoint"],
                access_token_data["token"],
                self.settings["matlab_version"],
            )
        except OnlineLicensingError as e:
            self.error = e
            log_error(logger, e)
            return False
        except EntitlementError as e:
            self.error = e
            log_error(logger, e)
            self.licensing["identity_token"] = None
            self.licensing["source_id"] = None
            self.licensing["expiry"] = None
            self.licensing["first_name"] = None
            self.licensing["last_name"] = None
            self.licensing["display_name"] = None
            self.licensing["user_id"] = None
            self.licensing["profile_id"] = None
            self.licensing["entitlements"] = []
            self.licensing["entitlement_id"] = None
            return False

        self.licensing["entitlements"] = entitlements

        # If there is only one non-expired entitlement, set it as active
        # TODO Also, for now, set the first entitlement as active if there are multiple
        self.licensing["entitlement_id"] = entitlements[0]["id"]

        # Successful update
        return True

    def persist_licensing(self):
        """Saves licensing information to file"""
        if self.licensing is None:
            self.__delete_cached_licensing_file()

        elif self.licensing["type"] in ["mhlm", "nlm"]:
            logger.info("Saving licensing information...")
            cached_licensing_file = self.__get_cached_licensing_file()
            cached_licensing_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cached_licensing_file, "w") as f:
                f.write(json.dumps(self.licensing))

    def reserve_matlab_port(self):
        """Reserve a free port for MATLAB Embedded Connector in the allowed range."""

        # FIXME Because of https://github.com/http-party/node-http-proxy/issues/1342 the
        # node application in development mode always uses port 31515 to bypass the
        # reverse proxy. Once this is addressed, remove this special case.
        if (
            mwi_env.is_development_mode_enabled()
            and not mwi_env.is_testing_mode_enabled()
        ):
            self.matlab_port = 31515
        else:

            # TODO If MATLAB Connector is enhanced to allow any port, then the
            # following can be used to get an unused port instead of the for loop and
            # try-except.
            # s.bind(("", 0))
            # self.matlab_port = s.getsockname()[1]
            for port in mw.range_matlab_connector_ports():
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.bind(("", port))
                    self.matlab_port = port
                    s.close()
                    break
                except socket.error as e:
                    if e.errno != errno.EADDRINUSE:
                        raise e

    async def start_matlab(self, restart=False):
        """Start MATLAB."""

        # FIXME
        if self.get_matlab_state() != "down" and restart is False:
            raise Exception("MATLAB already running/starting!")

        # FIXME
        if not self.is_licensed():
            raise Exception("MATLAB is not licensed!")

        if not self.is_matlab_present():
            self.error = MatlabInstallError("'matlab' executable not found in PATH")
            logger.error("'matlab' executable not found in PATH")
            self.logs["matlab"].clear()
            return

        if self.licensing["type"] == "mhlm":
            # Request an access token
            access_token_data = await mw.fetch_access_token(
                self.settings["mwa_api_endpoint"],
                self.licensing["identity_token"],
                self.licensing["source_id"],
            )

        # Ensure that previous processes are stopped
        await self.stop_matlab()

        # Clear MATLAB errors and logging
        self.error = None
        self.logs["matlab"].clear()

        # Reserve a port for MATLAB Embedded Connector
        self.reserve_matlab_port()

        # The presence of matlab_ready_file indicates if MATLAB Embedded Connector is
        # ready to receive connections, but this could be leftover from a terminated
        # MATLAB, so ensure it is cleaned up before starting MATLAB
        try:
            self.settings["matlab_ready_file"].unlink()
        except FileNotFoundError:
            pass

        # Configure the environment MATLAB needs to start
        matlab_env = os.environ.copy()
        matlab_env["MW_CRASH_MODE"] = "native"
        matlab_env["MATLAB_WORKER_CONFIG_ENABLE_LOCAL_PARCLUSTER"] = "true"
        matlab_env["PCT_ENABLED"] = "true"
        matlab_env["HTTP_MATLAB_CLIENT_GATEWAY_PUBLIC_PORT"] = "1"
        matlab_env["MW_CONNECTOR_SECURE_PORT"] = str(self.matlab_port)
        matlab_env["MW_DOCROOT"] = str(
            self.settings["matlab_path"] / "ui" / "webgui" / "src"
        )
        matlab_env["MWAPIKEY"] = self.settings["mwapikey"]
        # TODO Make this configurable (impacts the matlab ready file)
        matlab_env["MATLAB_LOG_DIR"] = "/tmp"
        matlab_env["MW_CD_ANYWHERE_ENABLED"] = "true"
        if self.licensing["type"] == "mhlm":
            matlab_env["MLM_WEB_LICENSE"] = "true"
            matlab_env["MLM_WEB_USER_CRED"] = access_token_data["token"]
            matlab_env["MLM_WEB_ID"] = self.licensing["entitlement_id"]
            matlab_env["MW_LOGIN_EMAIL_ADDRESS"] = self.licensing["email_addr"]
            matlab_env["MW_LOGIN_FIRST_NAME"] = self.licensing["first_name"]
            matlab_env["MW_LOGIN_LAST_NAME"] = self.licensing["last_name"]
            matlab_env["MW_LOGIN_DISPLAY_NAME"] = self.licensing["display_name"]
            matlab_env["MW_LOGIN_USER_ID"] = self.licensing["user_id"]
            matlab_env["MW_LOGIN_PROFILE_ID"] = self.licensing["profile_id"]
            if os.getenv(mwi_env.get_env_name_mhlm_context()) is None:
                matlab_env["MHLM_CONTEXT"] = "MATLAB_JAVASCRIPT_DESKTOP"

        elif self.licensing["type"] == "nlm":
            matlab_env["MLM_LICENSE_FILE"] = self.licensing["conn_str"]

        # Very verbose logging in debug mode
        if logger.isEnabledFor(logging.getLevelName("DEBUG")):
            matlab_env["MW_DIAGNOSTIC_DEST"] = "stdout"
            matlab_env[
                "MW_DIAGNOSTIC_SPEC"
            ] = "connector::http::server=all;connector::lifecycle=all"

        # TODO Introduce a warmup flag to enable this?
        # matlab_env["CONNECTOR_CONFIGURABLE_WARMUP_TASKS"] = "warmup_hgweb"
        # matlab_env["CONNECTOR_WARMUP"] = "true"

        # Start Xvfb process
        create_xvfb_cmd = self.settings["create_xvfb_cmd"]
        xvfb_cmd, dpipe = create_xvfb_cmd()

        xvfb, display_port = await mw.create_xvfb_process(xvfb_cmd, dpipe, matlab_env)

        # Update settings and matlab_env dict
        self.settings["matlab_display"] = ":" + str(display_port)
        self.processes["xvfb"] = xvfb

        matlab_env["DISPLAY"] = self.settings["matlab_display"]

        logger.debug(f"Started Xvfb with PID={xvfb.pid} on DISPLAY={display_port}")

        # Start MATLAB Process
        logger.info(f"Starting MATLAB on port {self.matlab_port}")
        master, slave = pty.openpty()
        matlab = await asyncio.create_subprocess_exec(
            *self.settings["matlab_cmd"],
            env=matlab_env,
            stdin=slave,
            stderr=asyncio.subprocess.PIPE,
        )
        self.processes["matlab"] = matlab
        logger.debug(f"Started MATLAB (PID={matlab.pid})")

        async def matlab_stderr_reader():
            logger.info("Starting task to save error logs from MATLAB")
            while not self.processes["matlab"].stderr.at_eof():
                logger.info("Checking for any error logs from MATLAB to save...")
                line = await self.processes["matlab"].stderr.readline()
                if line is None:
                    break
                logger.info("Saving error logs from MATLAB.")
                self.logs["matlab"].append(line)
            await self.handle_matlab_output()

        loop = asyncio.get_running_loop()
        self.tasks["matlab_stderr_reader"] = loop.create_task(matlab_stderr_reader())

    async def stop_matlab(self):
        """Terminate MATLAB."""

        matlab = self.processes["matlab"]
        xvfb = self.processes["xvfb"]

        waiters = []
        # Terminate
        if matlab is not None and matlab.returncode is None:
            logger.debug(f"Terminating MATLAB (PID={matlab.pid})")
            matlab.terminate()
            waiters.append(matlab.wait())

        if xvfb is not None and xvfb.returncode is None:
            logger.debug(f"Terminating Xvfb (PID={xvfb.pid})")
            xvfb.terminate()
            waiters.append(xvfb.wait())

        # Clean up matlab_ready_file
        try:
            with open(self.settings["matlab_ready_file"], "r") as mrf:
                port_in_matlab_ready_file = mrf.read()
                if str(self.matlab_port) == port_in_matlab_ready_file:
                    logger.info("Cleaning up matlab_ready_file...")
                    self.settings["matlab_ready_file"].unlink()
        except FileNotFoundError:
            # Some other process deleted this file
            pass

        # Wait for termination
        for waiter in waiters:
            await waiter

        # Clear logs if MATLAB stopped intentionally
        self.logs["matlab"].clear()

    async def handle_matlab_output(self):

        matlab = self.processes["matlab"]

        # Wait for MATLAB process to exit
        logger.info("handle_matlab_output Waiting for MATLAB to exit...")
        await matlab.wait()

        rc = self.processes["matlab"].returncode
        logger.info(f"handle_matlab_output MATLAB has exited with errorcode: {rc}")

        # Look for errors if MATLAB was not intentionally stopped and had an error code
        if len(self.logs["matlab"]) > 0 and self.processes["matlab"].returncode != 0:
            logger.info(f"handle_matlab_output Some error was found!")
            err = None
            logs = [log.decode().rstrip() for log in self.logs["matlab"]]

            def parsed_errs():
                if self.licensing["type"] == "nlm":
                    yield mw.parse_nlm_error(logs, self.licensing["conn_str"])
                if self.licensing["type"] == "mhlm":
                    yield mw.parse_mhlm_error(logs)
                yield mw.parse_other_error(logs)

            for err in parsed_errs():
                if err is not None:
                    break

            if err is not None:
                self.error = err
                log_error(logger, err)
