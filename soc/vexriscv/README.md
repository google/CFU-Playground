
## Custom VexRiscv

The VexRiscv Verilog files in this directory augment the ones provided in
`pythondata_cpu_vexriscv`.   This directory is a place to experiment
with new variants of VexRiscv.

PREREQUISITE 1: You must have the Scala build tool, `sbt`, installed and in your path.  One option is to follow the instructions under [Requirements](https://github.com/litex-hub/pythondata-cpu-vexriscv/blob/master/pythondata_cpu_vexriscv/verilog/README.md#requirements).  Ignore the material under 'Usages'; we will rebuild VexRiscv differently. Another option is to run `./scripts/setup_vexriscv_build.sh` from the root of this repository. This will install the needed tools to build new variants of Vexriscv. 


PREREQUISITE 2: Ensure that you have the VexRiscv source submodule loaded.   From the root of this repository, run `./scripts/setup`.


### Instructions

#### Option 1 (Manual)
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

* **Example**: See this [commit](https://github.com/google/CFU-Playground/pull/325/commits/e40b24f7499c9485dfe17d4bad1d2f9d1fd9713a)
  for a full example, including adding a new option to the Scala script.

#### Option 2 (Automated)

* You can also build a custom variant on demand from the command line which automatically takes care of the steps
  in Option 1. 

* At the command line simply assign values to the available VexRiscv parameters using the following syntax:
```
  EXTRA_LITEX_ARGS="--cpu-variant=generate+parameter1:value1+parameter2:value2...+parameterN:valueN"
```
  The keyword `generate` is needed at the beginning to signal the build. The list of avaiilable parameters and
  their default values can be found [here](https://github.com/google/CFU-Playground/blob/19e84323700c0eca521972436028acb912f5bcc8/soc/patch_cpu_variant.py#L148-L160). 
  
  *Note: To be consistent with legacy syntax the cfu parameter does not need to be assigned a value. Simply
   add* `+cfu` *to the end of your cpu variant to include the cfu or ignore it if you don't want to include it.*
  
* **Examples**

*Note: If a parameter is not specified, it takes on its default value.*

A Vexriscv variant without bypassing, a data cache size of 2048 bytes, and cfu included:
```
    make prog EXTRA_LITEX_ARGS="--cpu-variant=generate+bypass:false+dCacheSize:2048+cfu"
    make load EXTRA_LITEX_ARGS="--cpu-variant=generate+bypass:false+dCacheSize:2048+cfu"
```

A Vexriscv variant with static branch prediction, removes the hardware multiplier/divider, and does not include the cfu:
```
    make prog EXTRA_LITEX_ARGS="--cpu-variant=generate+prediction:static+mulDiv:false"
    make load EXTRA_LITEX_ARGS="--cpu-variant=generate+prediction:static+mulDiv:false"
```
For more information on possible parameter values, see the following [README](https://github.com/google/CFU-Playground/blob/main/proj/dse_template/README.md) used for exploring different Vexriscv variants.
