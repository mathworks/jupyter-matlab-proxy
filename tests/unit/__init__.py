# Copyright 2020-2023 The MathWorks, Inc.

"""Force Pytest to included untested files in coverage calculations.

Pytest won't include files in the coverage metrics unless they are imported in
the tests. By importing the systems under test here, any files not hit by a test
point are still included in the code coverage metrics.
"""
import jupyter_matlab_kernel
import jupyter_matlab_proxy
