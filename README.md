# CFU Playground

### Assumed Software

* RISC-V toolchain (riscv64-unknown-elf-*) tested w/ v9.1.0.   gcc v8.3 also works.  gcc v7.x is too old.

* openocd




### Setup

Clone this repo, `cd` into it, then get the first level of submodules (don't do `--recursive`):
```
git submodule init
git submodule update
```
### Use

Build the SoC in the `soc/` subdir, optionally with Etherbone, and load it onto Arty:
```
pushd soc
python3.7 ./soc.py --build --csr-csv csr.csv --cfu cfu/Cfu.v [--with-etherbone] --load
popd
```

Build the program and execute it:
```
cd basic_cfu
make
../soc/bin/litex_term --speed 115200 --kernel basic.bin /dev/ttyUSB*
```

TODO: make sure `lxterm` or `litex_term` are available on the user's path.

### Licensed under Apache-2.0 license

See the file `LICENSE`.
