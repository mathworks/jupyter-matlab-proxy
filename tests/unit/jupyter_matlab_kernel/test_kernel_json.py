# Copyright 2023-2025 The MathWorks, Inc.
import os
import shutil
import sys

import pytest
from jupyter_client.kernelspec import find_kernel_specs
from jupyter_matlab_kernel.kernelspec import install_kernel_spec

TEST_KERNEL_NAME = "jupyter_matlab_kernel_test"


@pytest.fixture
def UninstallKernel():
    yield
    kernel_list = find_kernel_specs()
    kernel_path = kernel_list.get(TEST_KERNEL_NAME)
    if kernel_path is not None and os.path.exists(kernel_path):
        shutil.rmtree(kernel_path)


def test_matlab_kernel_registration(tmp_path, UninstallKernel):
    """This test checks that the kernel.json file can be installed by JupyterLab."""

    install_kernel_spec(
        kernel_name=TEST_KERNEL_NAME,
        executable=sys.executable,
        kernelspec_dir=(tmp_path / TEST_KERNEL_NAME),
    )

    kernel_list = find_kernel_specs()

    assert TEST_KERNEL_NAME in kernel_list
