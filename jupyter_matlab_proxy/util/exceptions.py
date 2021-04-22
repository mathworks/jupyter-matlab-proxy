# Copyright 2020-2021 The MathWorks, Inc.


class AppError(Exception):
    def __init__(self, message, logs=None, stacktrace=None):
        self.message = message
        self.logs = logs
        self.stacktrace = stacktrace


class InternalError(AppError):
    pass


class MatlabInstallError(AppError):
    pass


class LicensingError(AppError):
    pass


class OnlineLicensingError(LicensingError):
    pass


class EntitlementError(OnlineLicensingError):
    pass


class NetworkLicensingError(LicensingError):
    pass


class NoAvailableNetworkLicensingError(NetworkLicensingError):
    pass


class MatlabError(AppError):
    pass


def log_error(logger, err):
    logs_str = ("\n" + "\n".join(err.logs)) if err.logs is not None else ""
    logger.error(err.message + logs_str)
