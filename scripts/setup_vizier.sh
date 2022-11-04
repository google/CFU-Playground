#!/bin/bash

CFU_ROOT="$(dirname $(dirname $(realpath ${BASH_SOURCE[0]})))"
VIZIER_DIR=${CFU_ROOT}/third_party/python/vizier

# Switch to Vizier repo before installing
cd ${VIZIER_DIR}
echo ""
echo "${VIZIER_DIR} found, installing Vizier"
echo ""

# This entire file installs core dependencies for OSS Vizier.
sudo apt-get install -y libprotobuf-dev  # Needed for proto libraries.

# Installs Python packages.
pip install -r requirements.txt --use-deprecated=legacy-resolver # Installs dependencies
pip install -e . # Installs Vizier

# Builds all .proto files.
./build_protos.sh

# Install Algo and Benchmark Dependencies
pip install -r requirements-algorithms.txt 
pip install -r requirements-benchmarks.txt 
cd ${CFU_ROOT}
