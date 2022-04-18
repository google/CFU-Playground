
## Custom VexRiscv

The VexRiscv Verilog files in this directory augment the ones provided in
`pythondata_cpu_vexriscv`.   This directory is a place to experiment
with new variants of VexRiscv.

PREREQUISITE 1: You must have the Scala build tool, `sbt`, installed and in your path.  One option is to follow the instructions under [Requirements](https://github.com/litex-hub/pythondata-cpu-vexriscv/blob/master/pythondata_cpu_vexriscv/verilog/README.md#requirements).  Ignore the material under 'Usages'; we will rebuild VexRiscv differently.


PREREQUISITE 2: Ensure that you have the VexRiscv source submodule loaded.   From the root of this repository, run `./scripts/setup`.


### Instructions

* To build a custom CPU, add a recipe to the Makefile in this directory (`soc/vexriscv/`).
  The target VexRiscv Verilog file should be named
  `VexRiscv_SomethingCfu.v` for CPUs with a CFU interface,
  or `VexRiscv_Something.v` for CPUs without a CFU interface,
  replacing "Something" with something meaningful.


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
    make TARGET=<target> EXTRA_LITEX_ARGS="--cpu-variant=something+cfu" bitstream
```


* Once you've generated a new custom CPU, you can add and commit to git
  the modified Makefile, the Scala script if modified,
  and both the new .v file and the accompanying new .yaml file.
  The new custom CPU can then be used by others, without the need for others to
  rerun the `sbt` build.

### Example

* See this [commit](https://github.com/google/CFU-Playground/pull/325/commits/e40b24f7499c9485dfe17d4bad1d2f9d1fd9713a)
  for a full example, including adding a new option to the Scala script.
