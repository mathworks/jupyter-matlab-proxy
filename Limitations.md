## Limitations

This package has some constraints and limitations:

* Notebooks running on the same server share the same MATLAB process and workspace. It is currently not possible to have separate workspaces for each notebook.

* Kernels cannot restart MATLAB automatically when users explicitly terminate their MATLAB session using the `exit` command or through the browser-based MATLAB development environment. Users must manually restart MATLAB using the options shown [here](https://github.com/mathworks/jupyter-matlab-proxy/blob/main/src/jupyter_matlab_proxy/README.md/#usage).

* The package does not support executing some MATLAB commands in notebooks. These include:

    * Commands that request input from users. For example: `input` and `keyboard`.

    * MATLAB debugging commands. For example: `dbstep`, `dbup`, and `dbstack`.

    * Commands that open another browser tab. For example: `doc` and `appdesigner`.

    * Commands that create animations. For example: `movie`.

    * **For MATLAB R2022a and earlier,** `lasterr` and `lasterror` do not capture MATLAB errors from execution in notebooks.

* Notebook results are truncated when there are more than 10 rows or 30 columns of results from MATLAB. This is represented by a `...` at the end of the result. For example:
    |![truncation-issue](https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/truncation-issue.png)|
    |-|

* Handles for graphics objects are scoped to a single cell in MATLAB versions <= R2023a. For example:
    |![invalid-handle](https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/invalid-handle.png)|
    |-|

* Graphics functions like `gca, gcf, gco, gcbo, gcbf, clf, cla`, which access `current` handles, are scoped to a single notebook cell in MATLAB versions <= R2023a. The following example illustrates this:
    |![gca-issue](https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/gca-issue.png)|
    |-|

* Notebooks do not show intermediate figures that were created during execution.

* Outputs from code cells are only displayed after the entire code cell has been run.

* MATLAB notebooks and MATLAB files do not autoindent after `case` statements.

* **For MATLAB R2024a and later,** tables are displayed as ASCII instead of HTML if the table meets any of the below conditions. Note that the below list is not exhaustive.
    * is an empty table
    * has more than 1000 rows
    * has more than 100 columns
    * has nested/grouped headers
    * has multi-column variables
    * is an event table
    * is a dataset

----

Copyright 2023-2024 The MathWorks, Inc.

----
