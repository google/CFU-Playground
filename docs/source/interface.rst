Details and Use Cases of the CPU <-> CFU interface
====================================================

After you have read the :doc:`overview <overview>` of the CFU Playground
components and :doc:`set up <setup-guide>` your CFU-Playground, and read
the :doc:`step-by-step guide <step-by-step>`, and you've decided to
build your CFU using Verilog, you will likely need more details of the 
timing at the CPU:CFU interface.   

This section will illustrate interface timing for some common cases.


-------------------------
Case 1: Combinational CFU
-------------------------

In the simplest CFU, there are no registers on the path from the operands (`cmd_inputs_0` and `cmd_inputs_1`)
to the result (`rsp_outputs_0`).   The result is computed based on the desired function specified by `cmd_function` and the operands.

.. wavedrom::

        { "signal": [
                { "name": "clk", "wave":       "P......." },
                { "name": "cmd_valid", "wave": "00100000" },
                { "name": "cmd_ready", "wave": "1......." },
                { "name": "cmd_function", "wave": "xx2xxxxx", data: ["fn"]  },
                { "name": "cmd_inputs_0", "wave": "xx3xxxxx", data: ["op1"] },
                { "name": "cmd_inputs_1", "wave": "xx4xxxxx", data: ["op2"] },
                {},
                { "name": "rsp_valid", "wave": "00100000" },
                { "name": "rsp_ready", "wave": "1......." },
                { "name": "rsp_outputs_0", "wave": "xx5xxxxx", phase: -0.1, data: ["rslt"] },
        ]}


-------------------------
Case 2: CFU with Latency
-------------------------

When the CFU computation critical path is more than will fit into one clock cycle,
the computation can be broken into stages.   After one or more clock cycles the result will be ready,
at which point the CFU asserts the `rsp_ready` signal.


.. note:: Note that the operands **and** the function specifier are valid only during one cycle. 
          It is the CFU's responsibility to grab and hold these values if needed until the computation finishes.
          These values can be held in registers enabled by the `cmd_valid` signal.

The latency from start to finish can be fixed or variable.   The CPU will stall as needed until
the result is produced and `rsp_valid` is asserted by the CFU.  
Of course, this means that a bug in your CFU may hang the CPU and entire system.

.. wavedrom::

        { "signal": [
                { "name": "clk", "wave":       "P......." },
                { "name": "cmd_valid", "wave": "00100000" },
                { "name": "cmd_ready", "wave": "1......." },
                { "name": "cmd_function", "wave": "xx2xxxxx", data: ["fn"] },
                { "name": "cmd_inputs_0", "wave": "xx3xxxxx", data: ["op1"] },
                { "name": "cmd_inputs_1", "wave": "xx4xxxxx", data: ["op2"] },
                {},
                { "name": "rsp_valid", "wave": "00001000" },
                { "name": "rsp_ready", "wave": "1......." },
                { "name": "rsp_outputs_0", "wave": "xxxx5xxx", phase: -0.1, data: ["rslt"] },
        ]}


-------------------------
Case 3: Split Phase
-------------------------

If the CFU operation is very long running, it might be useful to let the CPU carry on doing other work.  You can do this by using one instruction to start the operation (ignoring its results), and another instruction later to get the results.

If the CFU is not ready when the second instruction executes, the CPU will stall until it finishes.   The first instruction can be thought of as a "fork" and the second instruction as a "join" of control flow.  In the waveforms below, the CFU result *is* ready and is returned immediately when the second instruction executes.

Dashes ('--') below mean that the data value is ignored, i.e. a don't care.

.. wavedrom::

        { "signal": [
                { "name": "clk", "wave":       "P...|P..." },
                { "name": "cmd_valid", "wave": "0100|0010" },
                { "name": "cmd_ready", "wave": "1...|...." },
                { "name": "cmd_function", "wave": "x2xx|xx6x", data: ["fn1", "fn2"] },
                { "name": "cmd_inputs_0", "wave": "x3xx|xx=x", data: ["op1", "--"] },
                { "name": "cmd_inputs_1", "wave": "x4xx|xx=x" , data: ["op2", "--"]},
                {},
                { "name": "rsp_valid", "wave": "0100|0010" },
                { "name": "rsp_ready", "wave": "1...|...." },
                { "name": "rsp_outputs_0", "wave": "x=xx|xx9x", phase: -0.1, data: ["--", "rslt"] },
        ]}

--------------------------------
Case 4: More operands & results
--------------------------------

Some operations naturally have more than two operands and/or more than one result.
In this case, multiple CFU instructions can be used to move operands and fetch results.
One implementation option would be to use different opcodes for the different instructions.
Another option would be to have the CFU control keep track sequencing.

In the example below, three instructions use three different CFU opcodes.
The first instruction provides the first two operands and ignores the provided result.
The second instruction provides the rest of the operands, performs the computation, and returns the first result.
The third instruction provides the second result (operands are ignored).

.. wavedrom::

        { "signal": [
                { "name": "clk", "wave":          "P......" },
                { "name": "cmd_valid", "wave":    "0111000" },
                { "name": "cmd_ready", "wave":    "1......" },
                { "name": "cmd_function", "wave": "x269xxx" },
                { "name": "cmd_inputs_0", "wave": "x33=xxx", data: ["op1", "op3", "--"] },
                { "name": "cmd_inputs_1", "wave": "x34=xxx" , data: ["op2", "op4", "--"]},
                {},
                { "name": "rsp_valid", "wave":     "0111000" },
                { "name": "rsp_ready", "wave":     "1......" },
                { "name": "rsp_outputs_0", "wave": "x=55xxx", phase: -0.1, data: ["--", "rslt1", "rslt2"] },
        ]}

----------------------------------
Case 5: Addressable CFU registers
----------------------------------

For complex CFUs, it might make sense to have addressable storage or configuration registers.
Since the address is provided by an operand, you just need one opcode for writing to any
CFU register, and another opcode for reading from a CFU register.

In this example, the CPU writes values val0, val1, etc to CFU registers at indices 0, 1, etc.
It then issues an instruction telling the CFU to start its computation.
Later it reads back two values from the specified addresses.

.. wavedrom::

        { "signal": [
                { "name": "clk", "wave":           "P.......|...." },
                { "name": "cmd_valid", "wave":     "011|1010|0110" },
                { "name": "cmd_ready", "wave":     "1..|....|...." },
                { "name": "cmd_function", "wave":  "x22|2x4x|x55x", data: ["cfuw", "cfuwr", "cfuwr", "go", "cfurd", "cfurd"] },
                { "name": "cmd_inputs_0", "wave":  "x33|3x=x|x==x", data: ["0", "1", "15", "32", "33"] },
                { "name": "cmd_inputs_1", "wave":  "x33|3x=x|x==x", data: ["val0", "val1", "val15", "--", "--"] },
                {},
                { "name": "rsp_valid", "wave":     "011|1000|0110" },
                { "name": "rsp_ready", "wave":     "1..|....|...." },
                { "name": "rsp_outputs_0", "wave": "x==|=x=x|x66x", phase: -0.1, data: ["--", "--", "--", "--", "rslt1", "rslt2"] },
        ]}



----------------------------------
Case 6: Polling
----------------------------------

You might want to have the CPU check if the CFU is still working, and if it is, have the CPU continue working on other stuff.   This isn't possible with "Case 3" above since there's no way to check if the CFU is done without getting stuck waiting for it to finish.   The CFU can provide another instruction that simple returns True as a result if it is still busy.


.. wavedrom::

        { "signal": [
                { "name": "clk", "wave":           "P...|P..|P....." },
                { "name": "cmd_valid", "wave":     "0100|010|010010" },
                { "name": "cmd_ready", "wave":     ".1..|...|......" },
                { "name": "cmd_function", "wave":  "x2xx|x6x|x6xx7x", data: ["go", "busy?", "busy?", "cfurd"] },
                { "name": "cmd_inputs_0", "wave":  "x3xx|x=x|x=xx=x", data: ["op1", "--", "--", "--"] },
                { "name": "cmd_inputs_1", "wave":  "x4xx|x=x|x=xx=x" , data: ["op2", "--", "--", "--"]},
                {},
                { "name": "rsp_valid", "wave":     "0100|010|010010" },
                { "name": "rsp_ready", "wave":     "1...|...|......" },
                { "name": "rsp_outputs_0", "wave": "x=xx|x7x|x7xx8x", phase: -0.1, data: ["--", "T", "F", "rslt"] },
        ]}


----------------------------------
Case 7: Accumulation
----------------------------------

Another common case is when you want to shove an indefinite amount of data into the CFU, and the CFU keeps a running accumulation or reduction.  An example might be a dot product where you can send x[i] and y[i] for *i* from 0 to N-1.
This is usually implemented as 3 cooperating instructions: one to initialize the state (e.g. zero out the accumulator); one to send the next set of data; and a final one to retrieve the result.

On the software side, there is typically a loop streaming in the data -- reading values from memory and then executing the "acc" CFU instruction.   The "init" CFU instruction is executed before the loop is entered, and the "cfurd" CFU instruction is executed after the loop exits.


.. wavedrom::

        { "signal": [
                { "name": "clk", "wave":           "P....|P........" },
                { "name": "cmd_valid", "wave":     "01010|010010010" },
                { "name": "cmd_ready", "wave":     "1....|........." },
                { "name": "cmd_function", "wave":  "x2x6x|x6xx6xx7x", data: ["init", "acc", "acc", "acc", "cfurd"] },
                { "name": "cmd_inputs_0", "wave":  "x3x=x|x=xx=xx=x", data: ["--", "op1", "op61", "op63", "--"] },
                { "name": "cmd_inputs_1", "wave":  "x4x=x|x=xx=xx=x" , data: ["--", "op2", "op62", "op64", "--"]},
                {},
                { "name": "rsp_valid", "wave":     "01010|010010010" },
                { "name": "rsp_ready", "wave":     "1....|........." },
                { "name": "rsp_outputs_0", "wave": "x=x=x|x=xx=xx8x", phase: -0.1, data: ["--", "--", "--", "--", "rslt"] },
        ]}
