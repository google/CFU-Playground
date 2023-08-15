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

# Uncomment this line to use software defined CFU functions in software_cfu.cc
#DEFINES += CFU_SOFTWARE_DEFINED

# Uncomment this line to skip debug code (large effect on performance)
DEFINES += NDEBUG

# Uncomment this line to skip individual profiling output (has minor effect on performance).
#DEFINES += NPROFILE

# Uncomment to include specified model in built binary
DEFINES += INCLUDE_MODEL_PDTI8
#DEFINES += INCLUDE_MODEL_MICRO_SPEECH
#DEFINES += INCLUDE_MODEL_MAGIC_WAND
#DEFINES += INCLUDE_MODEL_MNV2
#DEFINES += INCLUDE_MODEL_HPS
#DEFINES += INCLUDE_MODEL_MLCOMMONS_TINY_V01_ANOMD
#DEFINES += INCLUDE_MODEL_MLCOMMONS_TINY_V01_IMGC
#DEFINES += INCLUDE_MODEL_MLCOMMONS_TINY_V01_KWS
#DEFINES += INCLUDE_MODEL_MLCOMMONS_TINY_V01_VWW

# Uncomment to include all TFLM examples (pdti8, micro_speech, magic_wand)
#DEFINES += INCLUDE_ALL_TFLM_EXAMPLES

# Uncomment this line to include the ASCII animated donut demo.
DEFINES += DONUT_DEMO

include ../proj.mk
