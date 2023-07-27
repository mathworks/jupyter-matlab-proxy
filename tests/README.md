# Testing Information for jupyter-matlab-proxy

The tests in this project are written using the [Pytest](https://docs.pytest.org/en/latest/) and [Unittest](https://docs.python.org/3/library/unittest.html) frameworks.

To run the tests in this project follow these steps:
* From the root directory of this project, run the command `python3 -m pip install ".[dev]"`
* Run the command `python3 -m pytest` to run all Python tests for this project.

## Integration testing with real MATLAB in the loop

These tests validate if the Jupyter Notebook Integration works well in presence of a real MATLAB. It covers running code in a jupyter notebook cell in an automated way without involving the UI.

### Test Requirements
1. MATLAB (Version >= `R2020b`) in the system path
2. MATLAB Proxy should be unlicensed
3. Run the following commands from the root directory of the project:
    ```
    python3 -m pip install .[dev]
    python3 -m playwright install --with-deps
    ```
4. MATLAB Proxy requirements
5. Jupyter MATLAB Proxy requirements

### How to run
* Run the following command from the root directory of the project:
    ```
    python3 -m pytest tests/integration
    ```

### Test Suite Setup
We use the [jupyter-kernel-test](https://github.com/jupyter/jupyter_kernel_test) python package and the [unittest](https://docs.python.org/3/library/unittest.html) testing framework in our tests.

The package `jupyter-kernel-test`, unfortunately, only considers the MATLAB Kernel as the system under test and does not communicate with [Jupyter Server](https://github.com/jupyter-server/jupyter_server) to query for running matlab-proxy processes. So, we must bypass Jupyter Server in our tests and establish a direct link between `jupyter-matlab-proxy` and `matlab-proxy`. We do this by starting an asynchronous matlab-proxy server in the test setup. The matlab-proxy configurations, such as app port, base URL etc., are passed as environment variables to the MATLAB Kernel, so it can use this server to serve MATLAB.

The licensing of MATLAB Proxy is done using the Playwright UI testing framework, where the MathWorks user credentials exist in environment variables.

### Test Suite Execution
1. These tests check the basic functionality that a jupyter kernel should support, i.e. running code, tab completion, printing a message, etc.
2. They also check some aspects specific to MATLAB Kernel, such as running the `ver` command, executing a MATLAB test file, plotting MATLAB figures etc.

### Test Suite Teardown
After the test execution ends, matlab-proxy is unlicensed, the corresponding process is terminated and all the environment variables set for testing purposes are unset to restore the system to the original state.


----

Copyright 2023 The Mathworks, Inc.

----