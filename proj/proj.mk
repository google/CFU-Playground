
SHELL           := /bin/bash
VIVADO_SETTINGS := /opt/Xilinx/Vivado/2019.1/settings64.sh

# TODO: search upward until we find the root
CFU_ROOT      := ../..
CFU_REAL_ROOT := $(realpath $(CFU_ROOT))

BUILD_DIR := ./build
GATEWARE  := $(BUILD_DIR)/gateware
SOFTWARE  := $(BUILD_DIR)/software
BITSTREAM := $(GATEWARE)/arty.bit

# Directory where we've already done a full Litex - Vivado build
GEN_SOC   := $(CFU_ROOT)/soc/build/arty/gateware
SOC_BASES := mem.init mem_1.init mem_2.init arty.v arty.tcl arty.xdc build_arty.sh
SOC_FILES := $(addprefix $(GEN_SOC)/, $(SOC_BASES))

PROJ_DIR    := .
CFU_VERILOG := $(PROJ_DIR)/cfu.v
REAL_CFU_VERILOG := $(realpath $(CFU_VERILOG))
SED_CFU_VERILOG := $(subst /,\/,$(REAL_CFU_VERILOG))
CFU_TFLM_DIR    := $(PROJ_DIR)/tflm_kernels
CFU_TFLM_FILES  := $(wildcard $(CFU_TFLM_DIR)/*)

CAM_BASES   := src ld Makefile
CAM_SRC_DIR := $(CFU_ROOT)/camera
CAM_FILES   := $(addprefix $(CAM_SRC_DIR)/, $(CAM_BASES))

LXTERM      := $(CFU_ROOT)/soc/bin/litex_term

soc: $(BITSTREAM)


#
# Copy necessary files from generic gateware build,
#   but replace the CFU and rerun Vivado
# NB: The arty.v copied here is NOT used.
#
$(BITSTREAM): $(SOC_FILES) $(CFU_VERILOG)
	@echo building SoC
	sleep 2
	mkdir -p $(GATEWARE)
	/bin/cp $(SOC_FILES) $(GATEWARE)
	sed -e 's/read_verilog {.*Cfu.v}/read_verilog {$(SED_CFU_VERILOG)}/' $(GATEWARE)/arty.tcl > /tmp/arty.tcl
	/bin/mv /tmp/arty.tcl $(GATEWARE)/arty.tcl
	pushd $(GATEWARE); source $(VIVADO_SETTINGS); source build_arty.sh; popd
	

prog: $(BITSTREAM)
	openocd -f $(CFU_REAL_ROOT)/prog/openocd_xc7_ft2232.cfg -c "init ; pld load 0 $(BITSTREAM) ; exit"

#
# Copy program sources and Makefile
# Add local (modified) versions of TFLM kernels to extra_src/ --
#    these will override the reference versions in libtflitemicro.a
#
sw:
	@echo building tflm camera app, under build/
	mkdir -p $(SOFTWARE)/camera
	/bin/cp -r $(CAM_FILES) $(SOFTWARE)/camera/
	mkdir -p $(SOFTWARE)/camera/extra_src
	/bin/cp $(CFU_TFLM_FILES) $(SOFTWARE)/camera/extra_src
	pushd $(SOFTWARE)/camera; make CFU_ROOT=$(CFU_REAL_ROOT); popd

load:
	$(LXTERM) --speed 115200 --kernel $(SOFTWARE)/camera/camera.bin /dev/ttyUSB1

load0:
	$(LXTERM) --speed 115200 --kernel $(SOFTWARE)/camera/camera.bin /dev/ttyUSB0


ls:
	ls -sAFC


clean:
	/bin/rm -rf ./build
