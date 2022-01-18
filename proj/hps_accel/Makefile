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

# Define which generation gateware to use = gen1 or gen2
#GATEWARE_GEN ?= 1
GATEWARE_GEN := 2
DEFINES += GATEWARE_GEN=$(GATEWARE_GEN)

# Uncomment these line to use the custom accelerated operations
DEFINES += ACCEL_CONV
DEFINES += ACCEL_PAD
DEFINES += ACCEL_MAX_POOL
DEFINES += ACCEL_FULLY_CONNECTED
DEFINES += ACCEL_STRIDED_SLICE

# For development purposes, dump a layer in accelerated code
# (Large effect on performance, much output)
#DEFINES += DUMP_LAYER=0

# Uncomment this line to use software defined CFU functions in software_cfu.cc
#DEFINES += CFU_SOFTWARE_DEFINED

# Uncomment to dump hashes of the output layer
#DEFINES += SHOW_OUTPUT_HASHES

# Uncomment this line to skip debug code (large effect on performance)
DEFINES += NDEBUG

# Show output from TF_LITE_ASSERTs
DEFINES += TF_LITE_MCU_DEBUG_LOG

# Uncomment this line to skip individual profiling output (has minor effect on performance).
#DEFINES += NPROFILE

# Uncomment to show the parameters used when evaluating a model
#DEFINES += SHOW_CONV_PARAMS
#DEFINES += SHOW_PAD_PARAMS
#DEFINES += SHOW_MAX_POOL_PARAMS
#DEFINES += SHOW_FULLY_CONNECTED_PARAMS
#DEFINES += SHOW_STRIDED_SLICE_PARAMS

# Hide progress dots (they mess up the formatting of CONV_PARAMS)
#DEFINES += HIDE_PROGRESS_DOTS

# Uncomment to include specified model in built binary
#DEFINES += INCLUDE_MODEL_PDTI8
#DEFINES += INCLUDE_MODEL_MICRO_SPEECH
#DEFINES += INCLUDE_MODEL_MAGIC_WAND
#DEFINES += INCLUDE_MODEL_MNV2
DEFINES += INCLUDE_MODEL_HPS
#DEFINES += INLCUDE_MODEL_MLCOMMONS_TINY_V01_ANOMD
#DEFINES += INLCUDE_MODEL_MLCOMMONS_TINY_V01_IMGC
#DEFINES += INLCUDE_MODEL_MLCOMMONS_TINY_V01_KWS
#DEFINES += INLCUDE_MODEL_MLCOMMONS_TINY_V01_VWW

# Uncomment to include all TFLM examples (pdti8, micro_speech, magic_wand)
#DEFINES += INCLUDE_ALL_TFLM_EXAMPLES

# Default is now hps proto2
# Use PLATFORM=common_soc TARGET=digilent_arty to select Arty instead of hps
PLATFORM=hps

# Parallel software and bitstream build
PARALLEL ?= no

# How to respond to run and test
RUN_MENU_ITEMS=1 1 c
TEST_MENU_ITEMS=3 q

# Customise arguments to Litex:
export EXTRA_LITEX_ARGS
export EXTRA_NEXTPNR_ARGS

# Use slim optimized core + CFU
EXTRA_LITEX_ARGS += --cpu-variant slimopt+cfu

# gen2 needs special build args and only works on hps
ifeq '$(GATEWARE_GEN)' '2'
EXTRA_LITEX_ARGS += --separate-arena --cfu-mport
export PLATFORM=hps
endif

ifeq '$(PLATFORM)' 'hps'
EXTRA_LITEX_ARGS += --parallel
endif

ifeq '$(TARGET)' 'digilent_arty'
# Cannot meet timing at 100MHz, reduce to 75MHz
EXTRA_LITEX_ARGS += --sys-clk-freq 75000000
endif

ifneq '$(PARALLEL)' 'no'
EXTRA_LITEX_ARGS += --extra-nextpnr-params
EXTRA_NEXTPNR_ARGS += --placer-heap-timingweight 79
endif

# Add constants defined in gateware/constants.py to C++ build
BUILD_DIR_EXTRA_DEP = $(BUILD_DIR)/src/gateware_constants.h

# Pass gen argument to cfu_gen
CFU_GEN_EXTRA_ARGS = gen$(GATEWARE_GEN)

BUILD_FLAGS="-j$(shell nproc)"

#### Base rules ####
include ../proj.mk

#### Additional rules ####

# Rule to build gateware_constants.h
$(BUILD_DIR)/src/gateware_constants.h: $(BUILD_DIR)/src $(PROJ_DIR)/gateware/gen$(GATEWARE_GEN)/constants.py
	$(PYRUN) -m gateware.gen$(GATEWARE_GEN).constants $@

all: bitstream software
