# Copyright 2023 The MathWorks, Inc.
import sys
from jupyter_client import kernelspec
import pytest
import os, shutil

TEST_KERNEL_NAME = "jupyter_matlab_kernel_test"


@pytest.fixture
def UninstallKernel():
    yield
    kernel_list = kernelspec.find_kernel_specs()
    kernel_path = kernel_list.get(TEST_KERNEL_NAME)
    if kernel_path != None and os.path.exists(kernel_path):
        shutil.rmtree(kernel_path)


def test_matlab_kernel_registration(UninstallKernel):
    """This test checks that the kernel.json file can be installed by JupyterLab."""

    kernelspec.install_kernel_spec(
        "./src/jupyter_matlab_kernel",
        kernel_name=TEST_KERNEL_NAME,
        prefix=sys.prefix,
    )

    kernel_list = kernelspec.find_kernel_specs()

    assert TEST_KERNEL_NAME in kernel_list
