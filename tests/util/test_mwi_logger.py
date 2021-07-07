# Copyright 2021 The MathWorks, Inc.
"""This file tests methods present in jupyter_matlab_proxy/util/mwi_logger.py
"""

import os
import logging
from jupyter_matlab_proxy.util import mwi_logger


def test_get():
    """This test checks if the get method returns a logger with expected name"""
    logger = mwi_logger.get()
    # Okay to use hidden API for testing only.
    assert logger.name == mwi_logger.__get_mw_logger_name()


def test_get_mw_logger_name():
    """Test to lock down the name of the logger used."""
    # Okay to use hidden API for testing only.
    assert "MATLABProxyApp" == mwi_logger.__get_mw_logger_name()


def test_get_with_no_environment_variables(monkeypatch):
    """This test checks if the get method returns a logger with default settings"""
    # Delete the environment variables if they do exist
    env_names_list = mwi_logger.get_environment_variable_names()
    monkeypatch.delenv(env_names_list[0], raising=False)
    monkeypatch.delenv(env_names_list[1], raising=False)

    logger = mwi_logger.get(init=True)
    assert logger.isEnabledFor(logging.INFO) == True
    assert len(logger.handlers) == 0


def test_get_with_environment_variables(monkeypatch, tmp_path):
    """This test checks if the get method returns a logger with default settings"""
    env_names_list = mwi_logger.get_environment_variable_names()
    monkeypatch.setenv(env_names_list[0], "CRITICAL")
    monkeypatch.setenv(env_names_list[1], str(tmp_path / "testing123.log"))

    logger = mwi_logger.get(init=True)

    # Verify that environment variable controlling level is respected
    assert logger.isEnabledFor(logging.CRITICAL) == True

    # Verify that environment variable setting the file is respected
    assert len(logger.handlers) == 1
    assert os.path.basename(logger.handlers[0].baseFilename) == "testing123.log"
