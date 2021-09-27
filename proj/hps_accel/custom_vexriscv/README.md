
## Project-specific Custom VexRiscv


* To build a custom CPU, just add a recipe in the Makefile in this directory.  The 
  target VexRiscv Verilog file must be named 
  `VexRiscv_CustomSomethingCfu.v` 
  or 
  `VexRiscv_CustomSomething.v`,
  for CPUs with and without a 
  CFU interface, respectively.  
  "Custom" must be part of the name.
  "Something" can be empty, or any CamelCasePhrase.


* The Makefile recipe allows you to select the parameters for each 
  custom CPU.  For examples showing many of the options, see the Makefile here:
  https://github.com/litex-hub/pythondata-cpu-vexriscv/blob/master/pythondata_cpu_vexriscv/verilog/Makefile,
  or look at the Scala script at `./src/main/scala/vexriscv/Custom.scala`.


* **Current restriction**: all custom CPUs must have a hard multiplier and divider (i.e.
  support the RISC-V 'm' extension).   The mul/div units do not need to be single-cycle, however.


* You can modify the Scala script at `./src/main/scala/vexriscv/Custom.scala` 
  to add more options to further control the CPU and its plugins.


* **To USE a custom variant**, use the existing `--cpu-variant` flag.  The
  mapping between the specified variant and the custom Verilog file is straightforward.
  The following specifies the use of `VexRiscv_CustomSomethingCfu.v`.
   
```
    make PLATFORM=hps EXTRA_LITEX_ARGS="--cpu-variant=custom+something+cfu" bitstream
```


* If the specified Verilog file does not exist, the build system 
  will attempt to `make` it using the Makefile.
  If the recipe for that Verilog file name exists,
  the recipe is executed, invoking `sbt`.


* Once you've generated a new custom CPU, you can add and commit both the .v file
  and the accompanying .yaml file to git.   The new custom CPU can then be used by others, 
  without the need for others to redo the `sbt` build.
