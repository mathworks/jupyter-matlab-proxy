#!/bin/bash
# Copyright 2024 The MathWorks, Inc.
# This script creates a container with The Littlest JupyterHub, and installs the MATLAB plugin tljh-matlab.
# To modify the MATLAB installation, update the .matlab_env file
# Update the last call to "docker exec" to customize your TLJH deployment.

# Example invocation:
# ./start-container-with-tljh-matlab.sh
## for Local Development of tljh-matlab
# ./start-container-with-tljh-matlab.sh --dev 1


# Initialize DEV flag
DEV=0

# Function to display usage
usage() {
  echo "Usage: $0 [-d 1|0] <command> [arguments...]"
  echo "  -d, --dev    Set development mode (1 for on, 0 for off). Default is OFF"
  exit 1
}

# Parse the arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -d|--dev)
      DEV="$2"
      if [[ "$DEV" != "1" && "$DEV" != "0" ]]; then
        echo "Error: DEV flag must be 1 or 0."
        usage
      fi
      shift 2
      ;;
    -*|--*)
      echo "Unknown option $1"
      usage
      ;;
    *)
      break
      ;;
  esac
done

set -e

# # Get the current working directory
CURRENT_DIR="$(pwd)"

if [ $(dirname "$0") != '.' ]; then
    PATH_TO_SCRIPTS="${CURRENT_DIR}/$(dirname "$0")"
    echo "Changing directory to ... $PATH_TO_SCRIPTS"
    pushd $PATH_TO_SCRIPTS
fi

# Create a Docker Container with systemd, named tljh-systemd
docker build -t tljh-systemd -f https://raw.githubusercontent.com/jupyterhub/the-littlest-jupyterhub/refs/heads/main/integration-tests/Dockerfile .

# By default, the plugin is pulled from PyPI.
MATLAB_PLUGIN_LOCATION="tljh-matlab"

# Start the tljh-systemd
docker run --privileged --detach --name=tljh-dev --publish 12000:80 --env-file .matlab_env tljh-systemd

# Get the latest TLJH sources from GitHub and move the code into /srv/src as required by the instructions in :
#   https://tljh.jupyter.org/en/latest/contributing/dev-setup.html
docker exec tljh-dev sh -c "cd /srv && git clone --depth 1 https://github.com/jupyterhub/the-littlest-jupyterhub.git && mv the-littlest-jupyterhub src"

if [ "$DEV" -eq 1 ]; then
    echo "Development mode is ON."
    MATLAB_PLUGIN_LOCATION="/tljh-matlab-local"    
    # Copy plugin sources to writable location within the container.
    docker container cp ./tljh-matlab tljh-dev:${MATLAB_PLUGIN_LOCATION}
fi

docker exec tljh-dev sh -c "python3 /srv/src/bootstrap/bootstrap.py --admin admin:password --plugin $MATLAB_PLUGIN_LOCATION"

popd