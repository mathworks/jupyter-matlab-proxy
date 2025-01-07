# Copyright 2024-2025 The MathWorks, Inc.

import pytest

from jupyter_matlab_kernel.jsp_kernel import MATLABKernelUsingJSP
from jupyter_matlab_kernel.kernel_factory import KernelFactory
from jupyter_matlab_kernel.mpm_kernel import MATLABKernelUsingMPM


@pytest.mark.parametrize(
    "env_value, expected_kernel_class",
    [
        pytest.param("TRUE", MATLABKernelUsingJSP, id="Default jupyter kernel"),
        pytest.param(
            "true", MATLABKernelUsingJSP, id="Case-insensitive match - jupyter kernel"
        ),
        pytest.param("FALSE", MATLABKernelUsingMPM, id="Using proxy manager"),
        pytest.param(
            "false", MATLABKernelUsingMPM, id="Case-insensitive match - proxy manager"
        ),
        pytest.param("TrUe", MATLABKernelUsingJSP, id="Mixed case"),
        pytest.param("", MATLABKernelUsingMPM, id="Empty string, use proxy manager"),
    ],
)
def test_correct_kernel_type_is_returned(monkeypatch, env_value, expected_kernel_class):
    """
    Test that the correct kernel type is returned based on the MWI_USE_FALLBACK_KERNEL environment variable.

    Args:
        monkeypatch: Pytest fixture for modifying the environment.
        env_value: The value to set for the MWI_USE_FALLBACK_KERNEL environment variable.
        expected_kernel_class: The expected kernel class to be returned.
    """
    monkeypatch.setenv("MWI_USE_FALLBACK_KERNEL", env_value)
    kernel_class = KernelFactory.get_kernel_class()
    assert kernel_class is expected_kernel_class


def test_correct_kernel_type_is_returned_when_env_var_unset(monkeypatch):
    """
    Test that the correct kernel type is returned when the MWI_USE_FALLBACK_KERNEL environment variable is unset.

    This test ensures that when the environment variable is not set, the default kernel class (MATLABKernelUsingJSP) is returned.

    Args:
        monkeypatch: Pytest fixture for modifying the environment.
    """
    monkeypatch.delenv("MWI_USE_FALLBACK_KERNEL", raising=False)
    kernel_class = KernelFactory.get_kernel_class()
    assert kernel_class is MATLABKernelUsingMPM
