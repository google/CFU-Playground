# CFU Playground

### Assumed Software

* [Vivado](https://www.xilinx.com/support/download.html) must be manually installed.

Other required packages will be checked for and, if on a Debian-based system,
automatically installed by the setup script below.

### Setup

Clone this repo, `cd` into it, then get run:
```sh
scripts/setup
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
cd proj/proj_template/basic_cfu/
make
make run
```

To run this basic program on a simulation of the SoC on your local machine,
execute:

```bash
make PROJ=proj_example sim-basic
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
