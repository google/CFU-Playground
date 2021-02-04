SHELL := /bin/bash

PROJ   ?= proj_template
MODEL  ?= pdti8

PROJ_DIR:=  $(abspath proj/$(PROJ))
CFU_V:=     $(PROJ_DIR)/cfu.v
CFU_SRCS:=  $(wildcard $(PROJ_DIR)/cfu.*)
CFU_ARGS:=  --cfu $(CFU_V)
SOC_NAME:=  arty.$(PROJ)
OUT_DIR:=   build/$(SOC_NAME)
CFU_ROOT:=  $(PWD)
PYRUN:=     $(CFU_ROOT)/scripts/pyrun

#UART_ARGS=  --uart-baudrate 115200
#UART_ARGS=  --uart-baudrate 460800
UART_ARGS=  --uart-baudrate 921600
LITEX_ARGS= --output-dir $(OUT_DIR) --csr-csv $(OUT_DIR)/csr.csv $(CFU_ARGS) $(UART_ARGS)


BITSTREAM:= soc/$(OUT_DIR)/gateware/arty.bit
LITEX_SW:=  soc/$(OUT_DIR)/software/include/generated/csr.h

.PHONY: soc prog harness run0 run1 b models projects harness-clean lsw

soc: $(BITSTREAM)

lsw: $(LITEX_SW)

$(CFU_V):
	pushd $(PROJ_DIR) && make cfu.v && popd


$(BITSTREAM): $(CFU_V) $(CFU_SRCS)
	@echo CFU option: $(CFU_ARGS)
	pushd $(PROJ_DIR) && make cfu.v && popd
	pushd soc && $(PYRUN) ./soc.py $(LITEX_ARGS) --build && popd

$(LITEX_SW):
	pushd soc && $(PYRUN) ./soc.py $(LITEX_ARGS) && popd

prog: $(BITSTREAM)
	pushd soc && $(PYRUN) ./soc.py $(LITEX_ARGS) --load && popd


harness: $(LITEX_SW)
	make -C $(PROJ_DIR) PROJ=$(PROJ) MODEL=$(MODEL) harness

harness-clean:
	make -C $(PROJ_DIR) PROJ=$(PROJ) MODEL=$(MODEL) harness-clean

run: $(BITSTREAM) prog
	make -C $(PROJ_DIR) PROJ=$(PROJ) MODEL=$(MODEL) run

renode: $(LITEX_SW)
	make -C $(PROJ_DIR) PROJ=$(PROJ) MODEL=$(MODEL) renode


sim-basic:
	pushd $(PROJ_DIR) && make sim-basic && popd

b:
	ls -lstr $(BITSTREAM)

models:
	@pushd models > /dev/null && ls && popd > /dev/null

projects:
	@pushd proj > /dev/null && ls -d proj_* && popd > /dev/null


