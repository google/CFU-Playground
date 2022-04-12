Details of the CPU <-> CFU interface
====================================================

After you have read the :doc:`overview <overview>` of the CFU Playground
components and :doc:`set up <setup-guide>` your CFU-Playground, and read
the :doc:`step-by-step guide <step-by-step>`, and you've decided to
build your CFU using Verilog, you will likely need more details of the 
timing at the CPU:CFU interface.   
This section will illustrate some common cases.


-------------------------
Case 1: Combinational CFU
-------------------------


.. wavedrom::

        { "signal": [
                { "name": "clk", "wave":       "P......." },
                { "name": "cmd_valid", "wave": "00100000" },
                { "name": "cmd_ready", "wave": "1......." },
                { "name": "cmd_function", "wave": "xx2xxxxx" },
                { "name": "cmd_inputs_0", "wave": "xx3xxxxx" },
                { "name": "cmd_inputs_1", "wave": "xx4xxxxx" },
                {},
                { "name": "rsp_valid", "wave": "00100000" },
                { "name": "rsp_ready", "wave": "1......." },
                { "name": "rsp_outputs_0", "wave": "xx5xxxxx", phase: -0.3 },
        ]}

