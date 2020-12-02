# CFU Playground

### Assumed Software

* RISC-V toolchain (riscv64-unknown-elf-*) tested w/ v8.3.0.  gcc v7.x is too old.   Also, header file incompatibilities have been seen with gcc v9.1.  So v8.3.0 is strongly recommended.
  * v8.3.0 is available at https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-8.3.0-2019.08.0-x86_64-linux-ubuntu14.tar.gz
  * Download the tar, ungzip and untar it, and put the `bin/` subdirectory in your PATH.

* `openocd`

* expect: `sudo apt install expect`

* Vivado


### Setup

Clone this repo, `cd` into it, then get the first level of submodules (don't do `--recursive`):
```
git submodule init
git submodule update
```
### Use

Build the SoC and load the bitstream onto Arty:
```
make PROJ=proj_template soc
make PROJ=proj_template prog
```
This builds the SoC with the default CFU from `proj/proj_template`.   Later you'll make your own project, and rerun those make commands with a modified `PROJ=proj_myproj` definition.


Build a basic program and execute it on the Arty board:
```
cd basic_cfu
make
../soc/bin/litex_term --speed 115200 --kernel basic.bin /dev/ttyUSB*
```

Build a TensorFlow Lite/Micro test harness executable and execute it on the Arty board (first `cd` to the repo root directory):

```
make PROJ=proj_template MODEL=pdti8 harness
make PROJ=proj_template MODEL=pdti8 run
```


### Underlying technology

* [LiteX](https://github.com/enjoy-digital/litex): Open-source framework for assembling the SoC (CPU + peripherals)
* [VexRiscv](https://github.com/SpinalHDL/VexRiscv): Open-source RISC-V soft CPU optimized for FPGAs


### Licensed under Apache-2.0 license

See the file `LICENSE`.
