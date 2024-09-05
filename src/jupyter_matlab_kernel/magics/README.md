# Magic Commands for MATLAB Kernel

You can use magic commands with the MATLAB kernel. You can use the predefined magic commands in this folder, and you can implement your own by following the steps below. 

## Get Started

Magic commands for the MATLAB kernel are prefixed with two percentage symbols `%%` without whitespaces. For example, to list available magic commands, run `%%lsmagic`

Note that magic commands will only work at the beginning of cells, and will not work with MATLAB variables.

The magic commands `help` and `file` accept additional parameters. For example, to display information about a magic command, run `%%help` followed by the name of the magic as an argument: `%%help time`

This table lists the predefined magic commands you can use: 


|Name|Description|Additional Parameters|Constraints|Example command|
|---|---|---|---|---|
|lsmagic|List predefined magic commands.|||`%%lsmagic`|
|help|Display information about provided magic command. | Name of magic command.|| `%%help file`|
|time|Display time taken to execute a cell.|||`%%time`|
|file|Save contents of cell as a file in the notebook folder. You can use this command to define and save new functions. For details, see the section below on how to [Create New Functions Using the %%file Magic Command](#create-new-functions-using-the-the-file-magic-command)|Name of saved file|The file magic command will save the contents of the cell, but not execute them in MATLAB|`%%file myfile.m`|


To request a new magic command, [create an issue](https://github.com/mathworks/jupyter-matlab-proxy/issues/new/choose).

## Create Your Own Magic Commands

To implement your own magic commands, follow these steps. You can use the predefined magic commands as examples.

1. In the `magics` folder, create a Python file with the name of your new magic command, for example `<new_magic_name>.py`.
2. Create a child class that inherits from the `MATLABMagic` class located in `jupyter_matlab_kernel/magics/base/matlab_magic.py` and modify these function members:
    1. info_about_magic
    2. skip_matlab_execution
    3. before_cell_execute
    4. after_cell_execute
    5. do_complete
   For details about these fields, see the descriptions in the `MATLABMagic` class.
3. Add tests for your magic command in the `tests/unit/jupyter_matlab_kernel/magics` folder.

## Create New Functions Using the the %%file Magic Command

In a notebook cell you can define MATLAB functions that are scoped to that cell. To define a function scoped to all the cells in a notebook, you can use the `%%file` magic command. Define a new function and save it as a MATLAB `.m` file, using the name of the function as the file name. For example, to create a function called `myAdditionFunction(x, y)`, follow these steps:

1. In a notebook cell, use the `%%file` command and define the function.

    ```
    %%file myAdditionFunction.m

    function addition = myAdditionFunction(x, y)
        addition = x + y;
    end
    ```

2. Run the cell to create a file called `myAdditionFunction.m` in the same folder as your notebook. 


3. You can then use this function in other cells of the notebook.

    ```
    addition = myAdditionFunction(3, 4);
    disp(addition)
    ```

Note: to use your function in MATLAB, remember to add the Jupyter notebook folder to the MATLAB path.

---

Copyright 2024 The MathWorks, Inc.

---
