# Copyright 2023 The MathWorks, Inc.
# Use ipykernel infrastructure to launch the MATLAB Kernel.

if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp
    from jupyter_matlab_kernel.kernel import MATLABKernel

    IPKernelApp.launch_instance(kernel_class=MATLABKernel)
