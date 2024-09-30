# Copyright 2023-2024 The MathWorks, Inc.
# Use ipykernel infrastructure to launch the MATLAB Kernel.
import os


def is_fallback_kernel_enabled():
    """
    Checks if the fallback kernel is enabled based on an environment variable.

    Returns:
        bool: True if the fallback kernel is enabled, False otherwise.
    """

    # Get the env var toggle
    use_fallback_kernel = os.getenv("MWI_USE_FALLBACK_KERNEL", "TRUE")
    return use_fallback_kernel.lower().strip() == "true"


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp
    from jupyter_matlab_kernel import mwi_logger

    logger = mwi_logger.get(init=True)
    kernel_class = None

    if is_fallback_kernel_enabled():
        from jupyter_matlab_kernel.jsp_kernel import MATLABKernelUsingJSP

        kernel_class = MATLABKernelUsingJSP
    else:
        from jupyter_matlab_kernel.mpm_kernel import MATLABKernelUsingMPM

        kernel_class = MATLABKernelUsingMPM

    IPKernelApp.launch_instance(kernel_class=kernel_class, log=logger)
