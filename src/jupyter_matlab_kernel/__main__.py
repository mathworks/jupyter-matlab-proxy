# Copyright 2023-2024 The MathWorks, Inc.
# Use ipykernel infrastructure to launch the MATLAB Kernel.

if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp
    from jupyter_matlab_kernel import mwi_logger
    from jupyter_matlab_kernel.kernel import MATLABKernel

    logger = mwi_logger.get(init=True)

    IPKernelApp.launch_instance(kernel_class=MATLABKernel, log=logger)
