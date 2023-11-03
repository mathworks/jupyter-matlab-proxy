# Testing Information for jupyter-matlab-proxy

The tests in this project are split into the categories of unit, integration, and
end-to-end level tests.

The unit tests are fast-running tests to validate the behaviour of individual
methods. Unit tests ensure small sections of the source code (units of code)
operate correctly.

The integration tests validate if the Jupyter® integration works well in the
presence of a real MATLAB®. It covers running code in a jupyter notebook cell in
an automated way without involving the UI.

The end-to-end tests start a JupyterLab instance and validate the behaviour of
jupyter-matlab-proxy via automated browser interactions. The end-to-end tests
are designed to ensure that common user workflows function as expected.


## Unit Tests

The unit tests are written using the
[Pytest](https://docs.pytest.org/en/latest/) and
[Unittest](https://docs.python.org/3/library/unittest.html) frameworks.

To run the unit tests in this project, follow these steps:
* From the root directory of this project, run the command
  ```
  python3 -m pip install ".[dev]"
  ```
* Run the command
  ```
  python3 -m pytest tests/unit
  ```

## Integration Tests

These tests validate if the Jupyter Notebook Integration works well in the
presence of a real MATLAB. It covers running code in a jupyter notebook cell in
an automated way without involving the UI. These tests use
[jupyter-kernel-test](https://github.com/jupyter/jupyter_kernel_test) python
package and the [unittest](https://docs.python.org/3/library/unittest.html)
testing framework in our integration tests.

Due to the architecture of `jupyter-matlab-proxy` and the fact that the package
`jupyter-kernel-test` does not communicate with [Jupyter
Server](https://github.com/jupyter-server/jupyter_server). We must bypass
Jupyter Server in our tests and establish a direct link between
`jupyter-matlab-proxy` and `matlab-proxy`.

We do this by starting an asynchronous matlab-proxy server in the test setup.
The matlab-proxy configurations, such as app port, base URL, etc., are passed as
environment variables to the MATLAB Kernel, so it can use this server to serve
MATLAB.

We then license MATLAB via MATLAB Proxy using the Playwright UI testing
framework, where the MathWorks® user credentials exist in environment variables.

This setup is done on a module level using Pytest. See the file conftest.py
inside the integration tests folder for details of all the fixtures.

### Integration test requirements
1. MATLAB (Version >= `R2020b`) in the system path
2. MATLAB Proxy should be unlicensed
3. Run the following commands from the root directory of the project:
    ```
    python3 -m pip install ".[dev]"
    python3 -m playwright install --with-deps
    ```
4. MATLAB Proxy requirements
5. Jupyter MATLAB Proxy requirements
6. Valid MathWorks Account credentials

### How to run the integration tests
* Set the environment variables TEST_USERNAME and TEST_PASSWORD to be your
  MathWorks Account user credentials.
    - Bash (Linux/macOS):
        ```bash
        TEST_USERNAME="some-username" && TEST_PASSWORD="some-password"
        ```
    - Powershell (Windows):
        ```powershell
        $env:TEST_USERNAME="some-username"; $env:TEST_PASSWORD="some-password"
        ```

* Run the following command from the root directory of the project:
    ```
    python3 -m pytest tests/integration
    ```



## End-to-End Tests

The end-to-end tests are written in TypeScript using the
[Playwright](https://playwright.dev/) framework. The reason these tests are
written in TypeScript and not in Python (using the pytest-playwright plugin for
example), is because these tests make use of [JupyterLab
Galata](https://github.com/jupyterlab/jupyterlab/tree/main/galata), which offers
a set of helpers and fixtures for JupyterLab UI exclusively in TypeScript.

### End-to-end test requirements
1. MATLAB (Version >= `R2020b`) in the system path
2. NodeJS version 18 or higher.
3. [MATLAB Proxy](https://github.com/mathworks/matlab-proxy) requirements
4. MATLAB Proxy should be unlicensed
6. Jupyter MATLAB Proxy requirements
7. Valid MathWorks Account credentials


### How to run the end-to-end tests
* Set the environment variables TEST_USERNAME and TEST_PASSWORD to be your
  MathWorks Account user credentials
    - Using a `.env` file (recommended):
      - Create a file called `.env` at the base of this repository, with the
        following lines:
        ```
        TEST_USERNAME="some-username"
        TEST_PASSWORD="some-password"
        ```
    - Bash (Linux/macOS):
        ```bash
        export TEST_USERNAME="some-username" && export TEST_PASSWORD="some-password"
        ```
        (if you don't want to use 'export' you can pass the environment
        variables in by prepending them to the Playwright test command below)
    - Powershell (Windows):
        ```powershell
        $env:TEST_USERNAME="some-username"; $env:TEST_PASSWORD="some-password"
        ```
* From the root directory of this project, install jupyter-matlab-proxy and
  JupyterLab with the command:
    ```
    pip install ".[dev]" "jupyterlab>=3.1.0,<4.0.0"
    ```
* From this repository's directory `/tests/e2e`, install the node packages using:
  ```
  npm install
  ```
  or to use the exact package version in the package-lock.json, use the command
  `npm ci` instead.
* Install the Playwright browsers with the command:
  ```
  npx playwright install
  ```
* Run the Playwright tests:
  ```
  npx playwright test
  ```
  If you don't want to use 'export' on your bash environment variables, you can pass in the
  variables like this:
  ```
  TEST_USERNAME="some-username" TEST_PASSWORD="some-password" npx playwright test
  ```

----

Copyright 2023 The MathWorks, Inc.

----
