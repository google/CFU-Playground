SHELL := /bin/bash

CFU_ARGS=   --cfu cfu/Cfu.v
UART_ARGS=  --uart-baudrate 460800
UART_ARGS=  --uart-baudrate 115200
LITEX_ARGS= --with-etherbone --csr-csv csr.csv $(CFU_ARGS) $(UART_ARGS)

.PHONY: build prog run0 run1

build:
	pushd soc; python3 ./soc.py $(LITEX_ARGS) --build; popd

prog:
	pushd soc; python3 ./soc.py $(LITEX_ARGS) --load; popd

camera/camera.bin:
	pushd camera; make; popd

run0: camera/camera.bin
	pushd camera; litex_term --kernel camera.bin /dev/ttyUSB0; popd

run1: camera/camera.bin
	pushd camera; litex_term --kernel camera.bin /dev/ttyUSB1; popd
