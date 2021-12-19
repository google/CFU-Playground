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

ifndef CFU_ROOT
  $(error CFU_ROOT must be set. $(HELP_MESSAGE))
endif

ifndef SOFTWARE_BIN
  $(error SOFTWARE_BIN must be set. $(HELP_MESSAGE))
endif

PROJ_DIR:=  $(CFU_ROOT)/proj/$(PROJ)
CFU_V:=     $(if $(wildcard $(PROJ_DIR)/cfu.sv), $(PROJ_DIR)/cfu.sv, $(PROJ_DIR)/cfu.v)
CFU_ARGS:=  --cpu-cfu $(CFU_V)

SOC_NAME:=  sim.$(PROJ)
OUT_DIR:=   build/$(SOC_NAME)
LITEX_ARGS= --output-dir $(OUT_DIR) \
	--csr-json $(OUT_DIR)/csr.json \
	$(CFU_ARGS) \
	--bin $(SOFTWARE_BIN) \
	--sim-trace

PYRUN:=     $(CFU_ROOT)/scripts/pyrun
SIM_RUN:=   MAKEFLAGS=-j8 $(PYRUN) ./sim.py $(LITEX_ARGS) $(EXTRA_LITEX_ARGS)
BIOS_BIN := $(OUT_DIR)/software/bios/bios.bin

.PHONY: run litex-software clean

litex-software: $(BIOS_BIN)

run: $(BITSTREAM)
	$(SIM_RUN) --run
	
clean:
	@echo Removing $(OUT_DIR)
	rm -rf $(OUT_DIR)

$(CFU_V):
	$(error $(CFU_V) not found. $(HELP_MESSAGE))

# we don't actually use the BIOS, but we do use all the other bits
# that are build along with it
$(BIOS_BIN): $(CFU_V)
	$(SIM_RUN) 
