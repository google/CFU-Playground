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
export PLATFORM   ?= arty

RUN_MENU_ITEMS    ?=1 1 1
TEST_MENU_ITEMS   ?=5

ifneq '' '$(fiter-out nexys_video,arty,sim,$(PLATFORM))'
	$(error PLATFORM must be 'arty' or 'nexys_video' or 'sim')
endif

SOC_DIR          := $(CFU_ROOT)/soc
SOC_BUILD_NAME   := $(PLATFORM).$(PROJ)
SOC_BUILD_DIR    := $(SOC_DIR)/build/$(SOC_BUILD_NAME)
SOC_SOFTWARE_DIR := $(SOC_BUILD_DIR)/software
export SOC_SOFTWARE_DIR
SOC_GATEWARE_DIR := $(SOC_BUILD_DIR)/gateware

# Make software build dependent on platform
export DEFINES    += PLATFORM_$(PLATFORM)
export DEFINES    += PLATFORM=$(PLATFORM)

SHELL           := /bin/bash
TTY             := $(wildcard /dev/ttyUSB?)
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

COMMON_DIR      := $(CFU_ROOT)/common
COMMON_FILES	:= $(shell find $(COMMON_DIR) -type f)
TFLM_SRC_DIR    := $(CFU_ROOT)/third_party/tflm_gen
SAXON_SRC_DIR   := $(CFU_ROOT)/third_party/SaxonSoc
SRC_DIR         := $(abspath $(PROJ_DIR)/src)

SOFTWARE_BIN     := $(BUILD_DIR)/software.bin
SOFTWARE_ELF     := $(BUILD_DIR)/software.elf
SOFTWARE_LOG     := $(BUILD_DIR)/software.log
UNITTEST_LOG     := $(BUILD_DIR)/unittest.log

# Directory where we build the project-specific gateware
SOC_DIR      := $(CFU_ROOT)/soc
ARTY_MK      := $(MAKE) -C $(SOC_DIR) -f $(SOC_DIR)/arty.mk
HPS_MK       := $(MAKE) -C $(SOC_DIR) -f $(SOC_DIR)/hps.mk
SIM_MK       := $(MAKE) -C $(SOC_DIR) -f $(SOC_DIR)/sim.mk SOFTWARE_BIN=$(SOFTWARE_BIN)
NEXYS_VIDEO_MK := $(MAKE) -C $(SOC_DIR) -f $(SOC_DIR)/nexys_video.mk
ifeq '$(PLATFORM)' 'arty'
	SOC_MK   := $(ARTY_MK)
else ifeq '$(PLATFORM)' 'nexys_video'
	SOC_MK   := $(NEXYS_VIDEO_MK)
else ifeq '$(PLATFORM)' 'hps'
	SOC_MK   := $(HPS_MK)
else ifeq '$(PLATFORM)' 'sim'
	SOC_MK   := $(SIM_MK)
else
	$(error PLATFORM must be 'arty' or 'nexys_video' or 'sim')
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
.PHONY: build-dir
build-dir:
	@echo Making BUILD_DIR
	mkdir -p $(BUILD_DIR)/src
	@# TFLM copied first due it having old/outdated copies of cfu.h etc
	@# that need to be overwritten
	$(COPY) $(TFLM_SRC_DIR)/*            $(BUILD_DIR)/src
	$(COPY) $(COMMON_DIR)/*              $(BUILD_DIR)
	$(COPY) $(SAXON_SRC_DIR)/riscv.h     $(BUILD_DIR)/src
	$(COPY) $(SRC_DIR)/*                 $(BUILD_DIR)/src
	$(RM)			             $(BUILD_DIR)/_*
ifneq ($(wildcard $(COMMON_DIR)/_$(PLATFORM)/*),)
	$(COPY) $(COMMON_DIR)/_$(PLATFORM)/* $(BUILD_DIR)
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
	@echo Running automated pdti8 test on Arty Board
	$(BUILD_DIR)/interact.expect $(SOFTWARE_BIN) $(TTY) $(UART_SPEED) $(RUN_MENU_ITEMS) |& tee $(SOFTWARE_LOG)

unit: $(SOFTWARE_BIN)
	@echo Running unit test on Arty Board
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
