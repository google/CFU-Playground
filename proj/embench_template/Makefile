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
#DEFINES += INCLUDE_MODEL_PDTI8
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

# Uncomment to include specified Embench workload in built binary
DEFINES += INCLUDE_EMBENCH_PRIMECOUNT 
#DEFINES += INCLUDE_EMBENCH_MINVER 
#DEFINES += INCLUDE_EMBENCH_AHA_MONT64
#DEFINES += INCLUDE_EMBENCH_CRC_32
#DEFINES += INCLUDE_EMBENCH_CUBIC
#DEFINES += INCLUDE_EMBENCH_EDN
#DEFINES += INCLUDE_EMBENCH_HUFFBENCH
#DEFINES += INCLUDE_EMBENCH_MATMUL
#DEFINES += INCLUDE_EMBENCH_MD5
#DEFINES += INCLUDE_EMBENCH_NBODY
#DEFINES += INCLUDE_EMBENCH_NETTLE_AES
#DEFINES += INCLUDE_EMBENCH_NETTLE_SHA256
#DEFINES += INCLUDE_EMBENCH_NSICHNEU
#DEFINES += INCLUDE_EMBENCH_PICOJPEG
#DEFINES += INCLUDE_EMBENCH_QRDUINO
#DEFINES += INCLUDE_EMBENCH_SLRE
#DEFINES += INCLUDE_EMBENCH_ST
#DEFINES += INCLUDE_EMBENCH_STATEMATE
#DEFINES += INCLUDE_EMBENCH_TARFIND
#DEFINES += INCLUDE_EMBENCH_UD
#DEFINES += INCLUDE_EMBENCH_WIKISORT

# Uncomment to include all Embench examples  
#DEFINES += INCLUDE_ALL_EMBENCH_EXAMPLES

# Uncomment to exclude TFLM src in build
#export SKIP_TFLM=1

include ../proj.mk
