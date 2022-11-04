#!/bin/env python
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This variable lists symbols to define to the C preprocessor
export DEFINES :=

# avg_pdti8 does not have a working software defined CFU
#DEFINES += CFU_SOFTWARE_DEFINED

# Uncomment this line to skip debug code (large effect on performance)
DEFINES += NDEBUG

# Uncomment this line to skip individual profiling output (has minor effect on performance).
DEFINES += NPROFILE

# Uncomment to include pdti8 in built binary
DEFINES += INCLUDE_MODEL_PDTI8

# output model parameters and weights
#DEFINES += SHOW_CONV_PARAMS
#DEFINES += SHOW_CONV_OUT_WEIGHTS

# Tests are in implementation files in this project
PYTEST_PATTERN := '*.py'

include ../proj.mk
