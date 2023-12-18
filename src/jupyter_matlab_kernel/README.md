# MATLAB Kernel for Jupyter

This module is a part of the `jupyter-matlab-proxy` package and it provides a Jupyter kernel for the MATLAB language.

## Usage

Upon successful installation of `jupyter-matlab-proxy`, your Jupyter environment should present several options for using MATLAB in Jupyter.

Click on `MATLAB Kernel` to create a Jupyter notebook for MATLAB.

|Jupyter Notebook| JupyterLab |
|--|--|
|<p align="center"><img width="200" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/classic-jupyter-kernel.png"></p> | <p align="center"><img width="500" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/jupyterlab_kernel_icon.png"></p> |

## Architecture

|![kernelArchitecture](https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/kernel-architecture.png)|
|-|

**Key takeaways:**

* When a notebook is opened, a new kernel is created for it.

* When the first execution request is made the following occurs:
    * A licensing screen is presented if this information has not been provided previously.
    * A MATLAB process is launched by Jupyter if one has not been launched previously.

* Every subsequent notebook does **not** ask for licensing information or launch a new MATLAB process.

* Every notebook communicates with MATLAB through the Jupyter notebook server.

* A notebook can be thought of as another view into the MATLAB process.
    * Any variables or data created through the notebook manifests in the spawned MATLAB process.
    * This implies that all notebooks access the same MATLAB workspace, and users must keep this in mind when working with multiple notebooks.

* If simultaneous execution requests are made from two notebooks, they are processed by MATLAB in a **first-in, first-out basis**.

* Kernel interrupts can be used to interrupt the execution that is currently being processed by MATLAB.

**Note**: If cells from multiple notebooks are being run at the same time, the execution request that gets interrupted may not be the one from which the interrupt was requested.

## Key Features
* Tab completion
* Execution of MATLAB code
* Rich outputs including:
    * Inline static plot images
    * LaTeX representation for symbolic expressions
* **For MATLAB R2022b and later:** Local functions can be defined at the end of a cell for use in the same cell
    <p><img src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/local_functions.png"></p>
* **For MATLAB R2024a and later:** Tables are formatted using HTML instead of ASCII
    | Before R2024a | After R2024a |
    |--|--|
    |<p align="center"><img width="550" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/tables_before_r2024a.png"></p> | <p align="center"><img width="500" src="https://github.com/mathworks/jupyter-matlab-proxy/raw/main/img/tables_after_r2024a.png"></p> |

## Limitations
Please refer to this [README](https://github.com/mathworks/jupyter-matlab-proxy#limitations) file for a listing of the current limitations. 

## Feedback

We encourage you to try this repository with your environment and provide feedback.
If you encounter a technical issue or have an enhancement request, create an issue [here](https://github.com/mathworks/jupyter-matlab-proxy/issues) or send an email to `jupyter-support@mathworks.com`

----

Copyright 2023 The MathWorks, Inc.

----
