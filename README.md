# CFU Playground

### Assumed Software

* RISC-V toolchain (riscv64-unknown-elf-*) tested w/ v9.1.0 and v8.3.0.  gcc v7.x is too old.
  * v8.3.0 is available at https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz

* openocd

* expect: `sudo apt install expect`



### Setup

Clone this repo, `cd` into it, then get the first level of submodules (don't do `--recursive`):
```
git submodule init
git submodule update
```
### Use

Build the SoC in the `soc/` subdir and load it onto Arty:
```
pushd soc
python3.7 ./soc.py --build --csr-csv csr.csv --cfu cfu/Cfu.v --load
popd
```

Build the program and execute it:
```
cd basic_cfu
make
../soc/bin/litex_term --speed 115200 --kernel basic.bin /dev/ttyUSB*
```


### Licensed under Apache-2.0 license

See the file `LICENSE`.
