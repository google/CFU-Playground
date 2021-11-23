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

# Uncomment this line to use software defined CFU functions in software_cfu.c
#DEFINES += CFU_SOFTWARE_DEFINED

# Uncomment this line to skip debug code (large effect on performance)
DEFINES += NDEBUG

# Uncomment this line to skip individual profiling output (has minor effect on performance).
#DEFINES += NPROFILE

# so that CI can make a SW-only version of the executable
#   (no custom instructions or CSRs)
ifdef SW_ONLY
DEFINES += NDEBUG NPROFILE CFU_SOFTWARE_DEFINED
endif

# Uncomment to include pdti8 in built binary
DEFINES += INCLUDE_MODEL_PDTI8

# Uncomment to include mnv2 in built binary (adds ~500kB to binary)
ifneq 'hps' '$(PLATFORM)'
DEFINES += INCLUDE_MODEL_MNV2
endif
RUN_MENU_ITEMS := 3 1

#DEFINES += SHOW_CONV_PARAMS
#DEFINES += SHOW_CONV_PERF
#DEFINES += SHOW_SAMPLE_POST_PROCESSING
#DEFINES += SHOW_MEMORY_USE

# Uncomment to use smaller batches for debugging. This helps expose 
# bugs with processing multiple batch handling.
#DEFINES += USE_CONV_SMALL_BATCHES

DEFINES += ACCEL_CONV

# Used by soc/hps.mk
# Choose the slimmer version of VexRiscv to fit with this large CFU
ifeq 'hps' '$(PLATFORM)'
export EXTRA_LITEX_ARGS='--cpu-variant=slim+cfu'
endif

include ../proj.mk
