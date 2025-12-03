# Copyright 2025 The MathWorks, Inc.

# Full image, with MATLAB and MATLAB Proxy

ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20
ARG NVM_VERSION="0.40.3"
ARG MATLAB_RELEASE="R2025b"
ARG UBUNTU_VERSION="24.04"
# Default installation directory for MATLAB
ARG MATLAB_INSTALL_LOCATION="/opt/matlab"
ARG MATLAB_PRODUCT_LIST="MATLAB"

FROM ubuntu:${UBUNTU_VERSION}

ARG NVM_VERSION
ARG PYTHON_VERSION
ARG NODE_VERSION
ARG MATLAB_RELEASE
ARG UBUNTU_VERSION
ARG MATLAB_INSTALL_LOCATION
ARG MATLAB_PRODUCT_LIST 

ENV DEBIAN_FRONTEND=noninteractive
# Install build dependencies, install UV (for python) and NVM (for nodejs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    unzip \
    xvfb \
    fluxbox \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

USER ubuntu

# Updates the default shell to bash instead of sh
SHELL ["/bin/bash", "-c"]

WORKDIR /home/ubuntu
# Set up development environment for ubuntu user with UV and NVM
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    source ${HOME}/.local/bin/env && \
    uv python install ${PYTHON_VERSION} && \
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh | bash  && \
    export NVM_DIR="/home/ubuntu/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && \
    nvm install ${NODE_VERSION} 

# Now the matlab-proxy directory can be mounted and tested for build

USER root

# Install MATLAB dependencies and MATLAB using MPM
ARG MATLAB_DEPS_URL="https://raw.githubusercontent.com/mathworks-ref-arch/container-images/main/matlab-deps/${MATLAB_RELEASE}/ubuntu${UBUNTU_VERSION}/base-dependencies.txt"
ARG MATLAB_DEPENDENCIES="matlab-deps-${MATLAB_RELEASE}-base-dependencies.txt"
ARG ADDITIONAL_PACKAGES="wget curl unzip ca-certificates xvfb git vim fluxbox gettext"
RUN export DEBIAN_FRONTEND=noninteractive && apt-get update \
    && apt-get install --no-install-recommends -y ${ADDITIONAL_PACKAGES}\
    && wget $(echo ${MATLAB_DEPS_URL} | tr "[:upper:]" "[:lower:]") -O ${MATLAB_DEPENDENCIES} \
    && xargs -a ${MATLAB_DEPENDENCIES} -r apt-get install --no-install-recommends -y \
    && apt-get clean \
    && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/* ${MATLAB_DEPENDENCIES}

WORKDIR /matlab-install
ARG MSH_MANAGED_INSTALL_ROOT=/usr/local/MathWorks/ServiceHost/
ARG MSH_DOWNLOAD_LOCATION=/tmp/Downloads/MathWorks/ServiceHost
# Dont need to set HOME to install Support packages as jupyter images set HOME to NB_USER in all images, even for ROOT.
RUN echo "Installing MATLAB using MPM..."
RUN wget -q https://www.mathworks.com/mpm/glnxa64/mpm && \ 
    chmod +x mpm \
    && ./mpm install --release=${MATLAB_RELEASE} --destination=${MATLAB_INSTALL_LOCATION} \
    --products ${MATLAB_PRODUCT_LIST} \
    || (echo "MPM Installation Failure. See below for more information:" && cat /tmp/mathworks_root.log && false)\
    && rm -f mpm /tmp/mathworks_root.log \
    && ln -s ${MATLAB_INSTALL_LOCATION}/bin/matlab /usr/local/bin/matlab \
    && git clone https://github.com/mathworks-ref-arch/administer-mathworks-service-host.git \
    && cd /matlab-install/administer-mathworks-service-host/admin-scripts/linux/admin-controlled-installation \
    && ./download_msh.sh --destination ${MSH_DOWNLOAD_LOCATION} \
    && ./install_msh.sh --source ${MSH_DOWNLOAD_LOCATION} --destination ${MSH_MANAGED_INSTALL_ROOT} --no-update-environment \
    && ./cleanup_default_msh_installation_location.sh --for-all-users \
    && cd / && rm -rf /matlab-install ${MSH_DOWNLOAD_LOCATION}

ENV MATHWORKS_SERVICE_HOST_MANAGED_INSTALL_ROOT=${MSH_MANAGED_INSTALL_ROOT}

USER ubuntu
WORKDIR /home/ubuntu
