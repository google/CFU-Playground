SHELL := /bin/bash

UART_ARGS=  --uart-baudrate 460800
UART_ARGS=  --uart-baudrate 115200
LITEX_ARGS= --with-etherbone --csr-csv csr.csv $(CFU_ARGS) $(UART_ARGS)

ifdef PROJ
PROJ_DIR:=  $(abspath proj/$(PROJ))
CFU:=       $(PROJ_DIR)/cfu.v
CFU_ARGS:=  --cfu $(CFU)
else
CFU_ARGS:=   --cfu cfu/Cfu.v
endif

.PHONY: build prog run0 run1

ifdef PROJ
build:
	@echo CFU option: $(CFU_ARGS)
	pushd $(PROJ_DIR); make cfu.v; popd
	pushd soc; python3 ./soc.py $(LITEX_ARGS) --build; /bin/cp -a build/arty build/arty_$(PROJ); popd
else
build:
	@echo CFU option: $(CFU_ARGS)
	pushd soc; python3 ./soc.py $(LITEX_ARGS) --build; popd
endif



prog:
	pushd soc; python3 ./soc.py $(LITEX_ARGS) --load; popd

camera/camera.bin:
	pushd camera; make; popd

run0: camera/camera.bin
	pushd camera; litex_term --kernel camera.bin /dev/ttyUSB0; popd

run1: camera/camera.bin
	pushd camera; litex_term --kernel camera.bin /dev/ttyUSB1; popd
