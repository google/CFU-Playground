# CFU Playground

Want a faster ML processor?   Do it yourself!

This project provides a framework that an engineer, intern, or student can use to design and evaluate **enhancements** to an FPGA-based “soft” processor, specifically to increase the performance of machine learning (ML) tasks.   The goal is to abstract away most infrastructure details so that the user can get up to speed quickly and focus solely on adding new processor instructions, exploiting them in the computation, and measuring the results.

This project enables rapid iteration on processor improvements -- multiple iterations per day.

This is how it works at the highest level:
* Choose a TensorFlow Lite model; a quantized person detection model is provided
* Execute the inference on the Arty board to get cycle counts per layer
* Choose an TFLite operator to accelerate, and dig into the code
* Design new instruction(s) that can replace multiple basic operations
* Modify the TFLite/Micro library kernel to use the new instruction(s), which are available as intrinsics using function call syntax.
* Rebuild the FPGA Soc, recompile the TFLM library, and rerun to measure improvement (simple `make` targets are provided)

The focus here is performance, not demos.  The inputs to the ML inference are canned/faked, and the only output is cycle counts.  It would be possible to export the improvements made here to an actual demo, but no pathway has been set up for doing so.

**Disclaimer: This is not an officially supported Google project.   Support and/or new releases may be limited.**

With the exception of Vivado, everything used by this project is open source.


### Required Hardware/OS

* Currently, the only supported target is the Arty 35T board from Digilent.
* The only supported host OS is Linux.

If you want to try things out using Renode simulation,
then you don't need either the Arty board or Vivado software.

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

### Underlying open-source technology

* [LiteX](https://github.com/enjoy-digital/litex): Open-source framework for assembling the SoC (CPU + peripherals)
* [VexRiscv](https://github.com/SpinalHDL/VexRiscv): Open-source RISC-V soft CPU optimized for FPGAs
* [nMigen](https://github.com/nmigen/nmigen): Python toolbox for building digital hardware


### Licensed under Apache-2.0 license

See the file [LICENSE](LICENSE).

### Contribution guidelines

**If you want to contribute to CFU Playground, be sure to review the
[contribution guidelines](CONTRIBUTING.md).  This project adheres to Google's
[code of conduct](CODE_OF_CONDUCT.md).   By participating, you are expected to
uphold this code.**



