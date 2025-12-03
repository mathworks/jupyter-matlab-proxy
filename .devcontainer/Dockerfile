# Copyright 2025 The MathWorks, Inc.

# Light weight image only to test builds of matlab-proxy

ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20
ARG NVM_VERSION="0.40.3"

FROM ubuntu:24.04

ARG NVM_VERSION
ARG PYTHON_VERSION
ARG NODE_VERSION

ENV DEBIAN_FRONTEND=noninteractive
# Install build dependencies, install UV (for python) and NVM (for nodejs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    unzip \
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


