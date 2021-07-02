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

# This Makefile builds the LiteX SoC.
#
# Typically, you would run 'make' in a project directory, which would use this Makefile recursively.
#

HELP_MESSAGE:= Run make from your project directory instead of using this file directly.

ifndef PROJ
  $(error PROJ must be set. $(HELP_MESSAGE))
endif

#ifndef UART_SPEED
#  $(error UART_SPEED must be set. $(HELP_MESSAGE))
#endif

ifndef CFU_ROOT
  $(error CFU_ROOT must be set. $(HELP_MESSAGE))
endif

PROJ_DIR:=  $(CFU_ROOT)/proj/$(PROJ)
CFU_V:=     $(PROJ_DIR)/cfu.v
CFU_ARGS:=  --cpu-cfu $(CFU_V)

SOC_NAME:=  hps.$(PROJ)
OUT_DIR:=   build/$(SOC_NAME)
# UART_ARGS=  --uart-baudrate $(UART_SPEED)
# LITEX_ARGS= --output-dir $(OUT_DIR) --csr-csv $(OUT_DIR)/csr.csv $(CFU_ARGS) $(UART_ARGS)
LITEX_ARGS= --output-dir $(OUT_DIR) --csr-csv $(OUT_DIR)/csr.csv $(CFU_ARGS)

#==== Specify a different synth tool; still uses Radiant PnR
ifdef USE_YOSYS
LITEX_ARGS += --synth_mode yosys
else ifdef USE_LSE
LITEX_ARGS += --synth_mode lse
endif

#==== Specify complete open source toolchain: Yosys + NextPnR
ifdef USE_OXIDE
LITEX_ARGS += --toolchain oxide
ifndef IGNORE_TIMING
LITEX_ARGS += --nextpnr-timingstrict
endif
else ifdef USE_SYMBIFLOW
LITEX_ARGS += --toolchain oxide
ifndef IGNORE_TIMING
LITEX_ARGS += --nextpnr-timingstrict
endif
endif

ifdef SLIM_CPU
LITEX_ARGS += --slim_cpu
endif

PYRUN:=     $(CFU_ROOT)/scripts/pyrun
HPS_RUN:=   MAKEFLAGS=-j8 $(PYRUN) ./hps_soc.py $(LITEX_ARGS)

BIOS_BIN := $(OUT_DIR)/software/bios/bios.bin
BITSTREAM:= $(OUT_DIR)/gateware/hps_platform.bit

.PHONY: bitstream litex-software prog clean

bitstream: $(BITSTREAM)

litex-software: $(BIOS_BIN)

prog: $(BITSTREAM)
	@echo Loading bitstream and bios onto HPS
	$(CFU_ROOT)/scripts/hps_prog $(BITSTREAM) bitstream
	$(CFU_ROOT)/scripts/hps_prog $(BIOS_BIN) program

clean:
	@echo Removing $(OUT_DIR)
	rm -rf $(OUT_DIR)

$(CFU_V):
	$(error $(CFU_V) not found. $(HELP_MESSAGE))

$(BIOS_BIN): $(CFU_V)
	$(HPS_RUN)

$(BITSTREAM): $(CFU_V)
	@echo Building bitstream for Arty. CFU option: $(CFU_ARGS)
	$(HPS_RUN) --build
