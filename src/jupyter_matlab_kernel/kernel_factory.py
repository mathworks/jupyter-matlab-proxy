# Copyright 2024-2025 The MathWorks, Inc.

import os
from typing import Union

from jupyter_matlab_kernel.jsp_kernel import MATLABKernelUsingJSP
from jupyter_matlab_kernel.mpm_kernel import MATLABKernelUsingMPM


class KernelFactory:
    """
    KernelFactory class for determining and returning the appropriate MATLAB kernel class.

    This class provides a static method to decide between different MATLAB kernel
    implementations based on configuration settings.
    """

    @staticmethod
    def _is_fallback_kernel_enabled():
        """
        Checks if the fallback kernel is enabled based on an environment variable.

        Returns:
            bool: True if the fallback kernel is enabled, False otherwise.
        """

        # Get the env var toggle
        use_fallback_kernel = os.getenv("MWI_USE_FALLBACK_KERNEL", "FALSE")
        return use_fallback_kernel.lower().strip() == "true"

    @staticmethod
    def get_kernel_class() -> Union[MATLABKernelUsingJSP, MATLABKernelUsingMPM]:
        """
        Determines and returns the appropriate MATLAB kernel class to use.

        Returns:
            BaseMATLABKernel: The class of the MATLAB kernel to be used. This will
            be either `MATLABKernelUsingJSP` if the fallback kernel is enabled,
            or `MATLABKernelUsingMPM` otherwise.
        """
        return (
            MATLABKernelUsingJSP
            if KernelFactory._is_fallback_kernel_enabled()
            else MATLABKernelUsingMPM
        )
