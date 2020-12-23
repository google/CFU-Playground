
SHELL           := /bin/bash

PROJ            := $(lastword $(subst /, ,${CURDIR}))
MODEL           ?= pdti8

TTY             := $(wildcard /dev/ttyUSB?)
UART_SPEED      := 115200
CRC             := --no-crc

#
# TODO: search upward until we find the root
# ... or get CFU_ROOT from an env variable
#
CFU_ROOT      := ../..
CFU_REAL_ROOT := $(realpath $(CFU_ROOT))


# Directory where we build the project-specific gateware
SOC_DIR   := $(CFU_ROOT)/soc
PLATFORM  := arty.$(PROJ)
GATEWARE  := $(SOC_DIR)/build/$(PLATFORM)/gateware
BITSTREAM := $(GATEWARE)/arty.bit


PROJ_DIR        := .
PROJ_REAL_DIR   := $(realpath $(PROJ_DIR))
CFU_NMIGEN      := $(PROJ_DIR)/cfu.py
CFU_NMIGEN_GEN  := $(PROJ_DIR)/cfu_gen.py
CFU_VERILOG     := $(PROJ_DIR)/cfu.v
BUILD           := $(PROJ_DIR)/build
THIRD_PARTY     := $(abspath $(PROJ_DIR)/third_party)
TFLM_DIR        := $(THIRD_PARTY)/tflm_gen
PYRUN           := $(CFU_REAL_ROOT)/scripts/pyrun

CAM_BASES   := src ld Makefile
CAM_SRC_DIR := $(CFU_ROOT)/camera
CAM_FILES   := $(addprefix $(CAM_SRC_DIR)/, $(CAM_BASES))

HARNESS_BASES   := src ld Makefile interact.expect
HARNESS_SRC_DIR := $(CFU_ROOT)/tflm_harness
HARNESS_FILES   := $(addprefix $(HARNESS_SRC_DIR)/, $(HARNESS_BASES))
HARNESS_DIR     := $(BUILD)/tflm_harness_$(MODEL)
HARNESS_BIN     := $(BUILD)/tflm_harness_$(MODEL)/tflm_harness.bin
HARNESS_LOG     := $(BUILD)/tflm_harness_$(MODEL)/$(MODEL).LOG

LXTERM      := $(CFU_ROOT)/soc/bin/litex_term


.PHONY:	proj harness-clean


soc: $(BITSTREAM)

#
# Copy necessary files from generic gateware build,
#   but replace the CFU and rerun Vivado
# NB: The arty.v copied here is NOT used.
#
$(BITSTREAM): $(CFU_VERILOG)
	@echo Building SoC
	make -C $(CFU_ROOT) PROJ=$(PROJ) soc

$(CFU_VERILOG): $(CFU_NMIGEN) $(CFU_NMIGEN_GEN)
	$(PYRUN) $(CFU_NMIGEN_GEN)

prog: $(BITSTREAM)
	openocd -f $(CFU_REAL_ROOT)/prog/openocd_xc7_ft2232.cfg -c "init ; pld load 0 $(BITSTREAM) ; exit"

sim-basic: $(CFU_VERILOG)
	pushd $(SOC_DIR) && $(PYRUN) ./soc.py --cfu $(PROJ_REAL_DIR)/$(CFU_VERILOG) --sim-rom-dir $(CFU_REAL_ROOT)/basic_cfu && popd

#
# Copy TFLM harness sources and Makefile.
# They will use this proj's tflm library.
#
harness: $(HARNESS_BIN)

$(HARNESS_BIN):
	@echo Building TFLM harness app, under build/, for model $(MODEL)
	mkdir -p $(HARNESS_DIR)
	/bin/cp -r $(HARNESS_FILES) $(HARNESS_DIR)
	make -C $(HARNESS_DIR) TFLM_DIR=$(TFLM_DIR) CFU_ROOT=$(CFU_REAL_ROOT) PLATFORM=$(PLATFORM) MODEL=$(MODEL) PROJ=$(PROJ)

harness-clean:
	/bin/rm -rf $(HARNESS_DIR)
	make -C $(TFLM_DIR) clean


#
# Copy program sources and Makefile
# TODO(avg): cam will will fail now
#
cam:
	@echo building tflm harness app, under build/, for model $(MODEL)
	mkdir -p $(BUILD)/camera
	/bin/cp -r $(CAM_FILES) $(BUILD)/camera/
	pushd $(BUILD)/camera; make TFLM_DIR=$(TFLM_DIR) CFU_ROOT=$(CFU_REAL_ROOT); popd

loadcam:
	$(LXTERM) --speed $(UART_SPEED) $(CRC) --kernel $(BUILD)/camera/camera.bin /dev/ttyUSB1

ifeq '1' '$(words $(TTY))'
load: $(HARNESS_BIN)
	$(LXTERM) --speed $(UART_SPEED) $(CRC) --kernel $(HARNESS_BIN) $(TTY)

run: $(HARNESS_BIN)
	$(HARNESS_DIR)/interact.expect $(HARNESS_BIN) $(TTY) |& tee $(HARNESS_LOG)

else
load:
	@echo Error: could not determine unique TTY
	@echo TTY possibilities: $(TTY)

run:
	@echo Error: could not determine unique TTY
	@echo TTY possibilities: $(TTY)

endif

        

ls:
	ls -sAFC


clean:
	/bin/rm -rf ./build

proj:
	echo $(PROJ)
