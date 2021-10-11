
## Custom VexRiscv

The VexRiscv Verilog files in this directory augment the one provided in 
`pythondata_cpu_vexriscv`.   This directory is a place to experiment
with new variants of VexRiscv.


* To build a custom CPU, add a recipe in the Makefile in this directory.  The
  target VexRiscv Verilog file should be named
  `VexRiscv_SomethingCfu.v` for CPUs with a CFU interface,
  or `VexRiscv_Something.v` for CPUs without a CFU interface.


* The Makefile recipe allows you to select the parameters for each
  custom CPU.  For examples showing many of the options, see the Makefile here:
  https://github.com/litex-hub/pythondata-cpu-vexriscv/blob/master/pythondata_cpu_vexriscv/verilog/Makefile,
  or look at the Scala script at `./src/main/scala/vexriscv/GenCoreDefault.scala`.


* You can modify the Scala script at `./src/main/scala/vexriscv/GenCoreDefault.scala`
  to add more options to further control the CPU and its plugins.



* **Make** your processor with the command `make VexRiscv_SomethingCfu.v`.   You must have `sbt` installed.



* **ADD** your new variant to the patching routine in $CFU_ROOT/soc/patch_cpu_variants.py.
  Try to use a variant name that corresponds to the file name you just created,
  for example "`something+cfu`" for `VexRiscv_SomethingCfu.v`.
  

* To **USE** a custom variant, use the existing `--cpu-variant` option.  The
  The following specifies the use of `VexRiscv_SomethingCfu.v`.
  
```
    make PLATFORM=hps EXTRA_LITEX_ARGS="--cpu-variant=something+cfu" bitstream
```


* Once you've generated a new custom CPU, you can add and commit to git
  the modified Makefile and both the .v file and the accompanying .yaml file.
  The new custom CPU can then be used by others, without the need for others to 
  redo the `sbt` build.
