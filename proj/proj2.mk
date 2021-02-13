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

export UART_SPEED ?= 921600
export PROJ       := $(lastword $(subst /, ,${CURDIR}))
export CFU_ROOT   := $(realpath $(CURDIR)/../..)
export PLATFORM   := arty.$(PROJ)

SHELL           := /bin/bash
MODEL           ?= pdti8

TTY             := $(wildcard /dev/ttyUSB?)
CRC             := --no-crc

#
# tools we use
COPY := /bin/cp -a
RM := /bin/rm -rf
MKDIR := /bin/mkdir

#
# TODO: search upward until we find the root
# ... or get CFU_ROOT from an env variable
#

# Directory where we build the project-specific gateware
SOC_DIR      := $(CFU_ROOT)/soc
SOC_MK       := $(MAKE) -C $(SOC_DIR) -f $(SOC_DIR)/soc.mk
GATEWARE_DIR := $(SOC_DIR)/build/$(PLATFORM)/gateware
BITSTREAM    := $(GATEWARE_DIR)/arty.bit

PROJ_DIR        := $(realpath .)
CFU_NMIGEN      := $(PROJ_DIR)/cfu.py
CFU_NMIGEN_GEN  := $(PROJ_DIR)/cfu_gen.py
CFU_VERILOG     := $(PROJ_DIR)/cfu.v
BUILD_DIR       := $(PROJ_DIR)/build
PYRUN           := $(CFU_ROOT)/scripts/pyrun

TFLM_SRC_DIR    := $(CFU_ROOT)/third_party/tflm_gen
SAXON_SRC_DIR   := $(CFU_ROOT)/third_party/SaxonSoc

TFLM_BLD_DIR    := $(abspath $(BUILD)/third_party/tflm_gen)
TFLM_OVERLAY_DIR:= $(abspath $(PROJ_DIR)/tflm_overlays)
TFLM_OVERLAYS   := $(shell find $(TFLM_OVERLAY_DIR) -type f 2>&1)

COMMON_DIR      := $(CFU_ROOT)/common
COMMON_FILES	:= $(shell find $(COMMON_DIR) -type f)
TFLM_SRC_DIR    := $(CFU_ROOT)/third_party/tflm_gen
SAXON_SRC_DIR   := $(CFU_ROOT)/third_party/SaxonSoc
SRC_DIR         := $(abspath $(PROJ_DIR)/src)

SOFTWARE_BIN     := $(BUILD_DIR)/software.bin
SOFTWARE_ELF     := $(BUILD_DIR)/software.elf

.PHONY:	renode 
renode: $(SOFTWARE_ELF) 
	@echo Running interactively under renode
	$(COPY) $(SOFTWARE_ELF) $(PROJ_DIR)/renode/
	pushd $(PROJ_DIR)/renode/ && renode -e "s @litex-vexriscv-tflite.resc" && popd

.PHONY: clean
clean:
	$(SOC_MK) clean
	@echo Removing $(BUILD_DIR)
	$(RM) $(BUILD_DIR)

.PHONY: software
software: $(SOFTWARE_BIN)

$(SOFTWARE_BIN) $(SOFTWARE_ELF): litex-software build-dir
	$(MAKE) -C build all

# Note that the common Makefile overwrites the TfLM Makefile
.PHONY: build-dir
build-dir:
	@echo Making BUILD_DIR
	mkdir -p $(BUILD_DIR)/src
	# TODO(avg): consider using rsync instead of cp
	$(COPY) $(COMMON_DIR)/*          $(BUILD_DIR)
	$(COPY) $(TFLM_SRC_DIR)/*        $(BUILD_DIR)/src
	$(COPY) $(SAXON_SRC_DIR)/riscv.h $(BUILD_DIR)/src
	$(COPY) $(SRC_DIR)/*             $(BUILD_DIR)/src

.PHONY: litex-software
litex-software:
	$(SOC_MK) litex-software

.PHONY: bitstream
bitstream: 
	$(SOC_MK) bitstream
	

.PHONY: load run
ifeq '1' '$(words $(TTY))'
run: $(SOFTWARE_BIN)
	@echo Running automated test on Arty Board
	$(HARNESS_DIR)/interact.expect $(HARNESS_BIN) $(TTY) |& tee $(HARNESS_LOG)

load: $(SOFTWARE_BIN)
	@echo Running interactively on Arty Board
	$(LXTERM) --speed $(UART_SPEED) $(CRC) --kernel $(HARNESS_BIN) $(TTY)

else
run load:
	@echo Error: could not determine unique TTY
	@echo TTY possibilities: $(TTY)

endif
