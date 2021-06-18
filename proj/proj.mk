#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.SHELL := /bin/bash

# Common build rules for all projects. Included by project makefiles.

# There are three execution environments supported by this makefile
#
# * Arty A7
# * Renode
# * Verilator simulation
#
# Arty builds require 3 parts:
# - SoC Gateware
# - SoC Software - BIOS, libraries and #includes
# - The main C program 
#
# Renode builds are quite similar to Arty, and use the same Soc Software
# and C program builds.
#
# Simulator builds are a little different:
# - Verilator C++ instead of Gateware
# - Soc Software is different due to the simulator having a different 
#   set of peripherals
# - The main C program requires rebuilding since it uses different Soc 
#   Software.
#
# To run on Arty (from within proj/xxx subdirectory):
# $ make prog    # Builds and programs gateware
# $ make load    # Builds and loads C program
#
# To run on Renode:
# $ make renode  # Builds and runs C program
#
# To run in simulation:
# $ make load PLATFORM=sim

export UART_SPEED ?= 3686400
export PROJ       := $(lastword $(subst /, ,${CURDIR}))
export CFU_ROOT   := $(realpath $(CURDIR)/../..)
export PLATFORM   ?= common_soc
export TARGET     ?= digilent_arty

RUN_MENU_ITEMS    ?=1 1 1
TEST_MENU_ITEMS   ?=5

PLATFORMS=common_soc sim hps
ifneq '$(PLATFORM)' '$(findstring $(PLATFORM),$(PLATFORMS))'
$(error PLATFORM must be one of following: $(PLATFORMS))
endif

ifneq 'common_soc' '$(PLATFORM)'
TARGET := $(PLATFORM)
endif

SOC_DIR          := $(CFU_ROOT)/soc
SOC_BUILD_NAME   := $(TARGET).$(PROJ)
SOC_BUILD_DIR    := $(SOC_DIR)/build/$(SOC_BUILD_NAME)
SOC_SOFTWARE_DIR := $(SOC_BUILD_DIR)/software
export SOC_SOFTWARE_DIR
SOC_GATEWARE_DIR := $(SOC_BUILD_DIR)/gateware

# Make software build dependent on platform
export DEFINES    += PLATFORM_$(PLATFORM)
export DEFINES    += PLATFORM=$(PLATFORM)

SHELL           := /bin/bash
TTY             := $(or $(wildcard /dev/ttyUSB?), $(wildcard /dev/ttyACM?))
CRC             := 
#CRC             := --no-crc

#
# tools we use
COPY := /bin/cp -a
RM := /bin/rm -rf
MKDIR := /bin/mkdir

#
# TODO: search upward until we find the root
# ... or get CFU_ROOT from an env variable
#

LXTERM       := $(SOC_DIR)/bin/litex_term
BITSTREAM    := $(SOC_GATEWARE_DIR)/$(PLATFORM).bit

PROJ_DIR        := $(realpath .)
CFU_GEN         := $(PROJ_DIR)/cfu_gen.py
CFU_VERILOG     := $(PROJ_DIR)/cfu.v
BUILD_DIR       := $(PROJ_DIR)/build
PYRUN           := $(CFU_ROOT)/scripts/pyrun

COMMON_DIR         := $(CFU_ROOT)/common
COMMON_FILES	   := $(shell find $(COMMON_DIR) -type f)
MLCOMMONS_SRC_DIR  := $(CFU_ROOT)/third_party/mlcommons
SAXON_SRC_DIR      := $(CFU_ROOT)/third_party/SaxonSoc
SRC_DIR            := $(abspath $(PROJ_DIR)/src)

TFLM_SRC_DIR       := $(CFU_ROOT)/third_party/tflite-micro
TFLM_MAKE_DIR      := $(TFLM_SRC_DIR)/tensorflow/lite/micro/tools/make

# Copy every file found in these directories, except those excluded
TFLM_COPY_SRC_DIRS := \
	tensorflow/lite \
	tensorflow/lite/c \
	tensorflow/lite/core/api \
	tensorflow/lite/kernels \
	tensorflow/lite/kernels/internal \
	tensorflow/lite/kernels/internal/optimized \
	tensorflow/lite/kernels/internal/reference \
	tensorflow/lite/kernels/internal/reference/integer_ops \
	tensorflow/lite/micro \
	tensorflow/lite/micro/kernels \
	tensorflow/lite/micro/memory_planner \
	tensorflow/lite/schema

TFLM_FIND_PARAMS := \
	-maxdepth 1 -type f \
	-not -name '*_test*' \
	-not -name 'space_to_depth.*' \
	-regex '.*\.\(h\|c\|cc\)'

# Just copy data files from these dirs
TFLM_COPY_DATA_DIRS := \
	tensorflow/lite/micro/benchmarks \
	tensorflow/lite/micro/examples/magic_wand \
	tensorflow/lite/micro/examples/micro_speech/micro_features \
	tensorflow/lite/micro/examples/person_detection \

SOFTWARE_BIN     := $(BUILD_DIR)/software.bin
SOFTWARE_ELF     := $(BUILD_DIR)/software.elf
SOFTWARE_LOG     := $(BUILD_DIR)/software.log
UNITTEST_LOG     := $(BUILD_DIR)/unittest.log

# Directory where we build the project-specific gateware
SOC_DIR      := $(CFU_ROOT)/soc
HPS_MK       := $(MAKE) -C $(SOC_DIR) -f $(SOC_DIR)/hps.mk
SIM_MK       := $(MAKE) -C $(SOC_DIR) -f $(SOC_DIR)/sim.mk SOFTWARE_BIN=$(SOFTWARE_BIN)
COMMON_SOC_MK := $(MAKE) -C $(SOC_DIR) -f $(SOC_DIR)/common_soc.mk

ifeq '$(PLATFORM)' 'hps'
	SOC_MK   := $(HPS_MK)
else ifeq '$(PLATFORM)' 'common_soc'
	SOC_MK   := $(COMMON_SOC_MK)
else ifeq '$(PLATFORM)' 'sim'
	SOC_MK   := $(SIM_MK)
else
	$(error PLATFORM must be 'arty' or 'nexys_video' or 'qmtech_wukong' or 'sim')
endif

.PHONY:	renode 
renode: $(SOFTWARE_ELF) 
	@echo Running interactively under renode
	$(COPY) $(SOFTWARE_ELF) $(PROJ_DIR)/renode/
	pushd $(PROJ_DIR)/renode/ && renode -e "s @litex-vexriscv-tflite.resc" && popd

.PHONY: clean
clean:
	$(SOC_MK) clean
	$(SIM_MK) clean
	@echo Removing $(BUILD_DIR)
	$(RM) $(BUILD_DIR)

.PHONY: software
software: $(SOFTWARE_BIN)

$(SOFTWARE_BIN) $(SOFTWARE_ELF): litex-software build-dir
	$(MAKE) -C $(BUILD_DIR) all

# Always run cfu_gen when it exists
# cfu_gen should not update cfu.v unless it has changed
ifneq (,$(wildcard $(CFU_GEN)))
$(CFU_VERILOG): generate_cfu

.PHONY: generate_cfu
generate_cfu:
	$(PYRUN) $(CFU_GEN)

endif

# Note that the common Makefile is used in preference to the TfLM Makefile
# TODO: consider using rsync instead of cp
#$(COPY) $(TFLM_SRC_DIR)/third_party  $(BUILD_DIR)/src/third_party
#	$(COPY) $(TFLM_SRC_DIR)/third_party  $(BUILD_DIR)/src/third_party

$(BUILD_DIR)/src:
	@echo "Making BUILD_DIR"
	@mkdir -p $(BUILD_DIR)/src

.PHONY: tflite-micro-src
tflite-micro-src: 
	@echo "Copying tflite-micro files"
	for d in $(TFLM_COPY_SRC_DIRS); do \
		mkdir -p $(BUILD_DIR)/src/$$d; \
		$(COPY) `find $(TFLM_SRC_DIR)/$$d $(TFLM_FIND_PARAMS)` $(BUILD_DIR)/src/$$d; \
	done
	$(COPY) $(TFLM_SRC_DIR)/tensorflow/lite/micro/kernels/conv_test* $(BUILD_DIR)/src/tensorflow/lite/micro/kernels
	$(COPY) $(TFLM_SRC_DIR)/tensorflow/lite/micro/kernels/depthwise_conv_test* $(BUILD_DIR)/src/tensorflow/lite/micro/kernels
	@for d in $(TFLM_COPY_DATA_DIRS); do \
		mkdir -p $(BUILD_DIR)/src/$$d; \
		$(COPY) `find $(TFLM_SRC_DIR)/$$d -maxdepth 1 -type f -regex '.*_data\.\(h\|cc\)'` $(BUILD_DIR)/src/$$d; \
	done
	$(COPY) $(TFLM_SRC_DIR)/tensorflow/lite/micro/examples/person_detection/model_settings* $(BUILD_DIR)/src/tensorflow/lite/micro/examples/person_detection

	@echo "TfLM: downloading third_party files"
	( cd $(TFLM_SRC_DIR); $(MAKE) -f $(TFLM_MAKE_DIR)/Makefile third_party_downloads )
	@echo "TfLM: copying selected third_party files"
	mkdir -p $(BUILD_DIR)/src/third_party/gemmlowp
	$(COPY) $(TFLM_MAKE_DIR)/downloads/gemmlowp/fixedpoint $(BUILD_DIR)/src/third_party/gemmlowp
	$(COPY) $(TFLM_MAKE_DIR)/downloads/gemmlowp/internal $(BUILD_DIR)/src/third_party/internal
	mkdir -p $(BUILD_DIR)/src/third_party/flatbuffers/include
	$(COPY) $(TFLM_MAKE_DIR)/downloads/flatbuffers/include/* $(BUILD_DIR)/src/third_party/flatbuffers/include
	mkdir -p $(BUILD_DIR)/src/third_party/ruy/ruy/profiler
	$(COPY) $(TFLM_MAKE_DIR)/downloads/ruy/ruy/profiler/instrumentation.h $(BUILD_DIR)/src/third_party/ruy/ruy/profiler
	$(COPY) $(TFLM_MAKE_DIR)/downloads/person_model_int8/* $(BUILD_DIR)/src/tensorflow/lite/micro/examples/person_detection

.PHONY: build-dir
build-dir: $(BUILD_DIR)/src tflite-micro-src
	@echo "build-dir: copying source to build dir"
	$(COPY) $(COMMON_DIR)/*              $(BUILD_DIR)
	$(COPY) $(MLCOMMONS_SRC_DIR)/*       $(BUILD_DIR)/src
	$(COPY) $(SAXON_SRC_DIR)/riscv.h     $(BUILD_DIR)/src
	$(COPY) $(SRC_DIR)/*                 $(BUILD_DIR)/src
	$(RM)			             $(BUILD_DIR)/_*
# Overlay platform / target specific changes.
ifneq ($(wildcard $(COMMON_DIR)/_$(PLATFORM)/$(TARGET)/*),)
	$(COPY) $(COMMON_DIR)/_$(PLATFORM)/$(TARGET)/* $(BUILD_DIR)
endif
	
.PHONY: litex-software
litex-software: $(CFU_VERILOG)
	$(SOC_MK) litex-software

RUN_TARGETS := load unit run
.PHONY: $(RUN_TARGETS) prog bitstream

ifneq 'sim' '$(PLATFORM)'
# $(PLATFORM) == 'arty'
prog: $(CFU_VERILOG)
	$(SOC_MK) prog

bitstream: $(CFU_VERILOG)
	$(SOC_MK) bitstream

ifeq '1' '$(words $(TTY))'
run: $(SOFTWARE_BIN)
	@echo Running automated pdti8 test on board
	$(BUILD_DIR)/interact.expect $(SOFTWARE_BIN) $(TTY) $(UART_SPEED) $(RUN_MENU_ITEMS) |& tee $(SOFTWARE_LOG)

unit: $(SOFTWARE_BIN)
	@echo Running unit test on board
	$(BUILD_DIR)/interact.expect $(SOFTWARE_BIN) $(TTY) $(UART_SPEED) $(TEST_MENU_ITEMS) |& tee $(UNITTEST_LOG)

ifeq 'hps' '$(PLATFORM)'
load: $(SOFTWARE_BIN)
	@echo Running interactively on HPS Board
	$(CFU_ROOT)/scripts/hps_prog $(SOFTWARE_BIN) program
	$(LXTERM) --speed 115200 $(TTY)

connect:
	@echo Connecting to HPS Board
	$(LXTERM) --speed 115200 $(TTY)
else
load: $(SOFTWARE_BIN)
	@echo Running interactively on FPGA Board
# Load hook allows common_soc.py to provide board-specific changes to load.
# This isn't ideal, the logic is starting to get too voluminous for a Makefile.
	$(SOC_MK) load_hook
	$(LXTERM) --speed $(UART_SPEED) $(CRC) --kernel $(SOFTWARE_BIN) $(TTY)
endif

else
$(RUN_TARGETS):
	@echo Error: could not determine unique TTY
	@echo TTY possibilities: $(TTY)
endif
else
# $(PLATFORM) == 'sim'
load: $(CFU_VERILOG) $(SOFTWARE_BIN)
	$(SIM_MK) run

unit: $(SOFTWARE_BIN)
	@echo Running unit test in Verilator simulation
	$(BUILD_DIR)/interact.expect s $(TEST_MENU_ITEMS) |& tee $(UNITTEST_LOG)

prog bitstream run:
	@echo Target not supported when PLATFORM=sim

endif

.PHONY: pytest
pytest:
	$(PYRUN) -m unittest discover -p '*.py'
