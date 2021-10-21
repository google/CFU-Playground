===============================
Customizing the CPU itself
===============================

It is very likely that after adding a CFU, you will want to fine tune 
the CPU (cache sizes, pipeline depth, etc.)  to give the best overall performance,
or possibly to free up some more resources to give to the CFU.
We use the VexRiscv processor, which was designed to map well to FPGAs and is very configurable.  
This section describes the steps required for "re-tuning" the CPU.



Detailed instructions
===================================

Go to the directory `soc/vexriscv` and follow the instructions in the 
`README.md <https://github.com/google/CFU-Playground/blob/main/soc/vexriscv/README.md>`_.
