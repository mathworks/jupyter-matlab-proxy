# Copyright 2023-2025 The MathWorks, Inc.
# Use ipykernel infrastructure to launch the MATLAB Kernel.

if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    from jupyter_matlab_kernel import mwi_logger
    from jupyter_matlab_kernel.kernel_factory import KernelFactory

    logger = mwi_logger.get(init=True)

    kernel_class = KernelFactory.get_kernel_class()
    logger.debug("Kernel type to be launched: %s", kernel_class)
    IPKernelApp.launch_instance(kernel_class=kernel_class, log=logger)
