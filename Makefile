SHELL := /bin/bash

PROJ   ?= proj_template
MODEL  ?= pdti8

PROJ_DIR:=  $(abspath proj/$(PROJ))
CFU_V:=     $(PROJ_DIR)/cfu.v
CFU_SRCS:=  $(wildcard $(PROJ_DIR)/cfu.*)
CFU_ARGS:=  --cfu $(CFU_V)
SOC_NAME:=  arty.$(PROJ)
OUT_DIR:=   build/$(SOC_NAME)

UART_ARGS=  --uart-baudrate 460800
UART_ARGS=  --uart-baudrate 115200
LITEX_ARGS= --output-dir $(OUT_DIR) --csr-csv csr.csv $(CFU_ARGS) $(UART_ARGS)


BITSTREAM:= soc/$(OUT_DIR)/gateware/arty.bit

.PHONY: soc prog harness run0 run1 b models projects

soc: $(BITSTREAM)

$(CFU_V):
	pushd $(PROJ_DIR) && make cfu.v && popd


$(BITSTREAM): $(CFU_V) $(CFU_SRCS)
	@echo CFU option: $(CFU_ARGS)
	pushd $(PROJ_DIR) && make cfu.v && popd
	pushd soc && python3 ./soc.py $(LITEX_ARGS) --build && popd


prog: $(BITSTREAM)
	pushd soc && python3 ./soc.py $(LITEX_ARGS) --load && popd


harness: $(BITSTREAM)
	make -C $(PROJ_DIR) PROJ=$(PROJ) MODEL=$(MODEL) harness

run: $(BITSTREAM) prog
	make -C $(PROJ_DIR) PROJ=$(PROJ) MODEL=$(MODEL) run


camera/camera.bin:
	pushd camera && make && popd

run0: camera/camera.bin
	pushd camera && litex_term --kernel camera.bin /dev/ttyUSB0 && popd

b:
	ls -lstr $(BITSTREAM)

models:
	@pushd models > /dev/null && ls && popd > /dev/null

projects:
	@pushd proj > /dev/null && ls -d proj_* && popd > /dev/null


