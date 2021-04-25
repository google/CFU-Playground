===============================
Customizing the CPU itself
===============================

It is very likely that after adding a CFU, the optimal configuration of the CPU 
(cache sizes, pipeline depth, etc.) will be different than when
the CPU did not have the CFU.

The CPU itself can be modified in many ways.  We use the VexRiscv processor,
which was designed to map well to FPGAs.  This section describes the steps 
required for "re-tuning" the CPU.


Git repository structure
=========================


* ``pythondata_cpu_vexriscv`` is a submodule of CFU Playground.
  We can focus on the contents of the directory at
  ``third_party/python/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv/verilog/``.
  It contains prebuilt Verilog for a number of different CPU variants,
  some CFU-enabled and some not.  
  The Makefile in this directory
  contains the command to rebuild each variant.
  Relative to this directory, the top Scala build script is for generating the CPU variants
  is at `src/main/scala/vexriscv/GenCoreDefault.scala`;
  this is invoked by the Makefile.
  To actually rebuild a variant, or build a new variant, you need to
  install the following submodule:

* ``VexRiscv`` is a submodule of ``pythondata_cpu_vexriscv``.
  It contains the *source code* for building the VexRisc CPU.  
  Normally it is not installed.   Instructions for installing it are located below.


Installing SBT and VexRiscv source
===================================

* Install ``java`` and ``sbt`` according to the instructions under `Requirements <https://github.com/litex-hub/pythondata-cpu-vexriscv/blob/master/pythondata_cpu_vexriscv/verilog/README.md#requirements>`_.
  The material under 'Usages' is outdated; we will rebuild VexRiscv differently.

* Install the VexRiscv source submodule:

  .. code:: bash

      cd third_party/python/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv/verilog
      git submodule update --init



* Check that things work by forcing a rebuild:

  .. code:: bash

      rm VexRiscv.v
      make VexRiscv.v


* You may see many warnings during the first build; that is normal.


* For help with VexRiscv, visit the chatroom at https://gitter.im/SpinalHDL/VexRiscv.



Modifying the default CPU variant, VexRiscv_FullCfu.v
======================================================

This is the best option for performing a quick experiment.

Find the lines in the Makefile for building VexRiscv_FullCfu.v:

.. code:: make

    VexRiscv_FullCfu.v: $(SRC)
           sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 8192 --iCacheSize 8192 --csrPluginConfig all --cfu true --perfCSRs 8 --outputFile VexRiscv_FullCfu"
 
Here, you can alter any of the options provided by the GenCoreDefault.scala script (note: if you specify --atomics or --compressedGen, you will need to figure out how to inform the compiler that the processor understands a different version of RV32):

 .. code::

    Usage: 
      -d | --debug
            Enable debug
      --iCacheSize <value>
            Set instruction cache size, 0 mean no cache
      --dCacheSize <value>
            Set data cache size, 0 mean no cache
      --mulDiv <value>
            set RV32IM
      --cfu <value>
            If true, add the CFU port
      --perfCSRs <value>
            Number of pausable performance counter CSRs to add (default 0)
      --atomics <value>
            set RV32I[A]
      --compressedGen <value>
            set RV32I[C]
      --singleCycleMulDiv <value>
            If true, MUL/DIV are single-cycle
      --singleCycleShift <value>
            If true, SHIFTS are single-cycle
      --relaxedPcCalculation <value>
            If true, one extra stage will be added to the fetch to improve timings
      --bypass <value>
            set pipeline interlock/bypass
      --externalInterruptArray <value>
            switch between regular CSR and array like one
      --dBusCachedRelaxedMemoryTranslationRegister <value>
            If set, it give the d$ its own address register between the execute/memory stage.
      --dBusCachedEarlyWaysHits <value>
            If set, the d$ way hit calculation is done in the memory stage, else in the writeback stage.
      --resetVector <value>
            Specify the CPU reset vector in hexadecimal. If not specified, an 32 bits input is added to the CPU to set durring instanciation
      --machineTrapVector <value>
            Specify the CPU machine trap vector in hexadecimal. If not specified, it take a unknown value when the design boot
      --prediction <value>
            Branch prediction choices: 'none', 'static', 'dynamic', 'dynamic_target'.  Default 'static'.
      --outputFile <value>
            output file name
      --csrPluginConfig <value>
            switch between 'small', 'all', 'linux' and 'linux-minimal' version of control and status registers configuration


After modifying the Makefile with altered/added options, simply remove and remake the target:

 .. code:: bash

     rm VexRiscv_FullCfu.v
     make VexRiscv_FullCfu.v


The Makefile doesn't have itself as a dependence for these targets, so modifying the Makefile isn't enough to trigger a rebuild.




Adding a new CPU variant to the Makefile
========================================

You may want to keep a number of alternatives around.   
Simply add new targets in the Makefile 
(copying all of the lines for the VexRiscv_FullCfu.v target, and updating the `--outputFile` option)
modified with your selected options; make them;
then alter the top SoC Python script (e.g. soc/arty.py) 
to choose among them.



Modifying the build script for access to more options
=====================================================

Not all possible VexRiscv options are currenly exposed as options to the `GenCoreDefault.scala` script.
Some of the options for the various plugins are hardcoded in the script, for example, 
the `DecoderSimplePlugin` sets `catchIllegalInstruction = true`.   
If you want to alter this (we're not suggesting that you do), you have two choices:

* Just edit the script to change it and then remake your VexRiscv, with the risk that you forget that you changed it.

* Add a new option to the script and use it to set the value, and then use this option in the Makefile for selected targets.


You can make much more drastic changes by choosing different plugins, or even writing your own.  
See https://github.com/SpinalHDL/VexRiscv for full VexRiscv documentation.


