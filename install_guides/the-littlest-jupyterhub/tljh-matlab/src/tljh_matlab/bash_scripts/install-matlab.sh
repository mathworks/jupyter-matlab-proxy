#!/bin/bash
# Copyright 2024 The MathWorks, Inc.

# Example invocation:
# subprocess.run(["bash", "install-matlab.sh"],
#                     env={"MATLAB_RELEASE":"R2024b", "MATLAB_PRODUCT_LIST":"MATLAB Simulink"})

# Set the default release to R2024b.
MATLAB_RELEASE="${MATLAB_RELEASE:-"R2024b"}"
# Uppercase first letter
MATLAB_RELEASE=${MATLAB_RELEASE^}

# Set the default product list to only install MATLAB.
MATLAB_PRODUCT_LIST="${MATLAB_PRODUCT_LIST:-"MATLAB Symbolic_Math_Toolbox"}"

MATLAB_INSTALL_DESTINATION="${MATLAB_INSTALL_DESTINATION:-"/opt/matlab/${MATLAB_RELEASE}"}"

echo "Installing..."
echo "MATLAB_RELEASE: $MATLAB_RELEASE"
echo "MATLAB_PRODUCT_LIST: $MATLAB_PRODUCT_LIST"
echo "MATLAB_INSTALL_DESTINATION: $MATLAB_INSTALL_DESTINATION"

env DEBIAN_FRONTEND="noninteractive" TZ="Etc/UTC" && apt-get update && apt-get install -y \
    ca-certificates \
    git \
    unzip \
    wget \
    xvfb  \
    && git clone --depth 1 https://github.com/mathworks/devcontainer-features \
    && env RELEASE="${MATLAB_RELEASE}" PRODUCTS="${MATLAB_PRODUCT_LIST}" DESTINATION="${MATLAB_INSTALL_DESTINATION}" \
    ./devcontainer-features/src/matlab/install.sh \
    && ln -s ${MATLAB_INSTALL_DESTINATION}/bin/matlab /usr/bin/matlab

# TLJH users dont have /usr/local/bin on the PATH, linking MATLAB into /usr/bin instead.