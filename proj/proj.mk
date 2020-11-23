
SHELL           := /bin/bash
VIVADO_SETTINGS := /opt/Xilinx/Vivado/2019.1/settings64.sh

# TODO: search upward until we find the root
CFU_ROOT := ../..

BUILD_DIR := ./build
GATEWARE  := $(BUILD_DIR)/gateware
BITSTREAM := $(GATEWARE)/arty.bit

# Directory where we've already done a full Litex - Vivado build
GEN_SOC   := $(CFU_ROOT)/soc/build/arty/gateware
SOC_BASES := mem.init mem_1.init mem_2.init arty.v arty.tcl arty.xdc build_arty.sh
SOC_FILES := $(addprefix $(GEN_SOC)/, $(SOC_BASES))

PROJ_DIR    := .
CFU_VERILOG := $(PROJ_DIR)/cfu.v
REAL_CFU_VERILOG := $(realpath $(CFU_VERILOG))
SED_CFU_VERILOG := $(subst /,\/,$(REAL_CFU_VERILOG))


soc: $(BITSTREAM)


# TODO: replace path to Cfu.v in arty.tcl with path to this project's CFU Verilog
$(BITSTREAM): $(SOC_FILES) $(CFU_VERILOG)
	@echo making SoC
	sleep 2
	mkdir -p $(GATEWARE)
	/bin/cp $(SOC_FILES) $(GATEWARE)
	sed -e 's/read_verilog {.*Cfu.v}/read_verilog {$(SED_CFU_VERILOG)}/' $(GATEWARE)/arty.tcl > /tmp/arty.tcl
	/bin/mv /tmp/arty.tcl $(GATEWARE)/arty.tcl
	pushd $(GATEWARE); source $(VIVADO_SETTINGS); source build_arty.sh; popd
	

load: $(BITSTREAM)

sw:
	@echo building tflm test
	@echo TBD

ls:
	ls -sAFC


clean:
	/bin/rm -rf ./build



