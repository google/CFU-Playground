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

ifndef UART_SPEED
  $(error UART_SPEED must be set. $(HELP_MESSAGE))
endif

ifndef CFU_ROOT
  $(error CFU_ROOT must be set. $(HELP_MESSAGE))
endif

PROJ_DIR:=  $(CFU_ROOT)/proj/$(PROJ)
CFU_V:=     $(PROJ_DIR)/cfu.v
CFU_ARGS:=  --cpu-cfu $(CFU_V)
TARGET_ARGS:= --target $(TARGET)
SOFTWARE_ARGS:= --software-load --software-path $(PROJ_DIR)/build/software.bin

SOC_NAME:=  $(TARGET).$(PROJ)
OUT_DIR:=   build/$(SOC_NAME)
UART_ARGS=  --uart-baudrate $(UART_SPEED)
LITEX_ARGS= --output-dir $(OUT_DIR) --csr-csv $(OUT_DIR)/csr.csv $(CFU_ARGS) $(UART_ARGS) $(TARGET_ARGS)

ifdef USE_SYMBIFLOW
LITEX_ARGS += --toolchain symbiflow
else 
ifdef USE_VIVADO
LITEX_ARGS += --toolchain vivado
endif
endif

PYRUN:=     $(CFU_ROOT)/scripts/pyrun
TARGET_RUN:=  MAKEFLAGS=-j8 $(PYRUN) ./common_soc.py $(LITEX_ARGS)

BIOS_BIN := $(OUT_DIR)/software/bios/bios.bin
BITSTREAM:= $(OUT_DIR)/gateware/$(TARGET).bit

.PHONY: bitstream litex-software load_hook prog clean check-timing

bitstream: $(BITSTREAM) check-timing

litex-software: $(BIOS_BIN)

ifdef USE_VIVADO
ifndef IGNORE_TIMING
check-timing:
	@echo Checking Vivado timing.
	@echo To disable this check, set IGNORE_TIMING=1
	@if grep -B 6 "Timing constraints are not met" $(OUT_DIR)/gateware/vivado.log  ; then exit 1 ; fi
else
check-timing:
	@echo Vivado timing check is skipped.
endif
else
check-timing:
	@echo Timing check performed only for Vivado.
endif

load_hook:
	$(TARGET_RUN) $(SOFTWARE_ARGS)

prog: $(BITSTREAM) check-timing
	@echo Loading bitstream onto board
	$(TARGET_RUN) --no-compile-software --load

clean:
	@echo Removing $(OUT_DIR)
	rm -rf $(OUT_DIR)

$(CFU_V):
	$(error $(CFU_V) not found. $(HELP_MESSAGE))

$(BIOS_BIN): $(CFU_V)
	$(TARGET_RUN)

$(BITSTREAM): $(CFU_V)
	@echo Building bitstream for $(TARGET). CFU option: $(CFU_ARGS)
	$(TARGET_RUN) --build
