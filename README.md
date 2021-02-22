# CFU Playground

### Assumed Software

* [Vivado](https://www.xilinx.com/support/download.html) must be manually installed.

Other required packages will be checked for and, if on a Debian-based system,
automatically installed by the setup script below.

TODO: describe how to install renode.

### Setup

Clone this repo, `cd` into it, then get run:
```sh
scripts/setup
```
### Use

Build the SoC and load the bitstream onto Arty:
```sh
cd proj/proj_template
make prog
```
This builds the SoC with the default CFU from `proj/proj_template`.   Later you'll make your own project, and rerun those make commands with a modified `PROJ=proj_myproj` definition.


Build a program and execute it on the SoC you just loaded onto the Arty
```sh
make load
```

To use renode to execute on a simulator on your own machine, execute:

```sh
make renode
```

### Underlying technology

* [LiteX](https://github.com/enjoy-digital/litex): Open-source framework for assembling the SoC (CPU + peripherals)
* [VexRiscv](https://github.com/SpinalHDL/VexRiscv): Open-source RISC-V soft CPU optimized for FPGAs


### Licensed under Apache-2.0 license

See the file [LICENSE](LICENSE).

### Contribution guidelines

**If you want to contribute to CFU Playground, be sure to review the
[contribution guidelines](CONTRIBUTING.md).  This project adheres to Google's
[code of conduct](CODE_OF_CONDUCT.md).   By participating, you are expected to
uphold this code.**



