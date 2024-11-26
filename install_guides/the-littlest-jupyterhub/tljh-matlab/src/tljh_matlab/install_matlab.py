# Copyright 2024 The MathWorks, Inc.

import subprocess
import os

# @package install_matlab
#  This module provides functionalities to install MATLAB using a bash script.


def install_matlab_impl():
    """
    @brief Installs MATLAB using a predefined bash script.

    This function constructs the path to a bash script responsible for installing MATLAB and executes it.
    The MATLAB release and product list are specified through environment variables. If not present, defaults are used.

    @param None
    @return None
    """
    # Construct the path to the install script
    script = os.path.join(os.path.dirname(__file__), "bash_scripts/install-matlab.sh")

    # Call the bash script with environment variables
    subprocess.run(
        [
            "bash",
            script,
        ],
        env=os.environ,
    )


if __name__ == "__main__":
    install_matlab_impl()
