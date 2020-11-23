SHELL := /bin/bash

CFU_ARGS=   --cfu cfu/Cfu.v
LITEX_ARGS= --with-etherbone --csr-csv csr.csv $(CFU_ARGS)


build:
	cd soc; python3 ./soc.py $(LITEX_ARGS) --build; cd ..

prog:
	cd soc; python3 ./soc.py $(LITEX_ARGS) --load; cd ..

camera/camera.bin:
	pushd camera; make; popd

run0: camera/camera.bin
	pushd camera; litex_term --kernel camera.bin /dev/ttyUSB0; popd

run1: camera/camera.bin
	pushd camera; litex_term --kernel camera.bin /dev/ttyUSB1; popd
