The Step-by-Step Guide to Building an ML Accelerator
====================================================

After you have read the :doc:`overview <overview>` of the CFU Playground
components and :doc:`set up <setup-guide>` your CFU-Playground, it's time
to accelerate a model. This tutorial will walk through the steps for building
a basic CFU in your choice of Amaranth or Verilog.

-------------------------
Step 1: Make Your Project
-------------------------

You'll be building an accelerator in your own project folder. Navigate to the
root of your CFU-Playground directory and enter the following in your terminal:

.. code-block:: bash

    $ cp -r proj/proj_template proj/my_first_cfu
    $ cd proj/my_first_cfu

Now that you've made a project folder you can choose what model you'd like to
accelerate. In the project folder you just made, open the Makefile and you
should see something like this:

.. code-block:: bash

    # This variable lists symbols to define to the C preprocessor
    export DEFINES :=

    # Uncomment this line to use software defined CFU functions in software_cfu.cc
    #DEFINES += CFU_SOFTWARE_DEFINED

    # Uncomment this line to skip debug code (large effect on performance)
    DEFINES += NDEBUG

    # Uncomment this line to skip individual profiling output (has minor effect on performance).
    #DEFINES += NPROFILE

    # Uncomment to include pdti8 in built binary
    DEFINES += INCLUDE_MODEL_PDTI8

    # Uncomment to include micro_speech in built binary
    #DEFINES += INCLUDE_MODEL_MICRO_SPEECH

    #...

By uncommenting lines in this Makefile you can add specific models to your
build (you can also remove models by re-commenting the lines).

By default only the ``pdti8`` model is configured as part of the build. If you
can fit this model on your board (if you're using the Arty you can), we
recommend using it for this tutorial.

-----------------------------------------------
Step 2: Profile and Identify What to Accelerate
-----------------------------------------------

Now that we've set up our project, we should start by measuring the performance
of the software unmodified to both understand what we should accelerate and get
a baseline performance reading.

In your project folder (``proj/my_first_cfu``) run the following:

.. code-block:: bash

    $ make prog  # if you're not using the arty add TARGET=<your board>
    $ make load  # if you're not using the arty add TARGET=<your board>

After the build processes are completed you should see something like the
following in your terminal:

::

    CFU Playground
    ==============
    1: TfLM Models menu
    2: Functional CFU Tests
    3: Project menu
    4: Performance Counter Tests
    5: TFLite Unit Tests
    6: Benchmarks
    7: Util Tests

Navigate to the your model's menu by entering ``1``, then ``1`` in the
menus. Once at the model menu (shown below) press ``g`` to run the golden
tests.

::

    Tests for pdti8 model
    =====================
    1: Run with zeros input
    2: Run with no-person input
    3: Run with person input
    g: Run golden tests (check for expected outputs)
    x: eXit to previous menu
    pdti8> g

After running the golden tests you should have some output that looks like
this:

::

    "Event","Tag","Ticks"
    0,DEPTHWISE_CONV_2D,7892
    1,DEPTHWISE_CONV_2D,8063
    2,CONV_2D,11703
    3,DEPTHWISE_CONV_2D,4089
    4,CONV_2D,8264
    5,DEPTHWISE_CONV_2D,8045
    6,CONV_2D,13234
    7,DEPTHWISE_CONV_2D,2041
    8,CONV_2D,6618
    9,DEPTHWISE_CONV_2D,4065
    10,CONV_2D,11637
    11,DEPTHWISE_CONV_2D,1011
    12,CONV_2D,5955
    13,DEPTHWISE_CONV_2D,1923
    14,CONV_2D,11611
    15,DEPTHWISE_CONV_2D,1919
    16,CONV_2D,11601
    17,DEPTHWISE_CONV_2D,1939
    18,CONV_2D,11628
    19,DEPTHWISE_CONV_2D,1943
    20,CONV_2D,11619
    21,DEPTHWISE_CONV_2D,1925
    22,CONV_2D,11624
    23,DEPTHWISE_CONV_2D,509
    24,CONV_2D,5859
    25,DEPTHWISE_CONV_2D,922
    26,CONV_2D,11257
    27,AVERAGE_POOL_2D,51
    28,CONV_2D,14
    29,RESHAPE,1
    30,SOFTMAX,11
     Counter |  Total | Starts | Average |     Raw
    ---------+--------+--------+---------+--------------
        0    |     0  |     0  |   n/a   |            0
        1    |     0  |     0  |   n/a   |            0
        2    |     0  |     0  |   n/a   |            0
        3    |     0  |     0  |   n/a   |            0
        4    |     0  |     0  |   n/a   |            0
        5    |     0  |     0  |   n/a   |            0
        6    |     0  |     0  |   n/a   |            0
        7    |     0  |     0  |   n/a   |            0
       183M (   183328857) cycles total

The comma-separated lines at the top signify the TensorFlow operation and the
number of "ticks" it took to complete. Each tick counted by the profiler is
1024 clock cycles. For easier analysis, you can copy and paste these values
into a spreadsheet that you maintain whilst performing optimizations.

The table at the bottom shows statistics from the performance CSRs (if you
turned them on), the final line shows the total number of cycles spent during
inference.

Summing up all the cycle counts for the tensorFlow operations we see that
about 75% of the time is spent inside the ``CONV_2D`` operation. That seems
like a good place to focus our optimization efforts on.

To further profile ``CONV_2D``, let's use the performance counters inside the
source code.

Inside your project folder run the following:

.. code-block:: bash

    $ mkdir -p src/tensorflow/lite/kernels/internal/reference/integer_ops/
    $ cp \
      ../../third_party/tflite-micro/tensorflow/lite/kernels/internal/reference/integer_ops/conv.h \
      src/tensorflow/lite/kernels/internal/reference/integer_ops/conv.h

This will create a copy of the convolution source code in your project
directory. At build time your copy of the source code will replace the regular
implementation.

Open the newly created copy at ``proj/my_first_cfu/src/tensorflow/lite/kernels/
internal/reference/integer_ops/conv.h``. The pdti8 model uses the first
function in this file. Locate the innermost loop of the first function, it
should look something like this:

.. code-block:: C++

    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      int32_t input_val = input_data[Offset(input_shape, batch, in_y,
                                              in_x, in_channel)];
      int32_t filter_val = filter_data[Offset(
          filter_shape, out_channel, filter_y, filter_x, in_channel)];
        /* ... */
      acc += filter_val * (input_val + input_offset);
    }

To count how many cycles this inner loop takes you can utilize the performance
counters built into the soft-CPU. Add ``#include "perf.h"`` at the top of the
file and then surround the inner loop with perf functions like below:

.. code-block:: C++

    #include "perf.h"
    /* ... */
    perf_enable_counter(0);
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      int32_t input_val = input_data[Offset(input_shape, batch, in_y,
                                              in_x, in_channel)];
      int32_t filter_val = filter_data[Offset(
          filter_shape, out_channel, filter_y, filter_x, in_channel)];
        /* ... */
      acc += filter_val * (input_val + input_offset);
    }
    perf_disable_counter(0);

Re-build the projects (``make load``) and run the golden tests again, the table
at the end of the terminal output should now look something like this:

::

    Counter |  Total | Starts | Average |     Raw
    ---------+--------+--------+---------+--------------
        0    |   113M | 124418  |   908   |    113064622
        1    |     0  |     0  |   n/a   |            0
        2    |     0  |     0  |   n/a   |            0
        3    |     0  |     0  |   n/a   |            0
        4    |     0  |     0  |   n/a   |            0
        5    |     0  |     0  |   n/a   |            0
        6    |     0  |     0  |   n/a   |            0
        7    |     0  |     0  |   n/a   |            0

If you don't see any numbers in the first row of the table add some print
statements inside the function to check if you're editing in the correct place.
If those print statements execute but the performance counters still don't
count, your FPGA board could be so resource-constrained as to not have room for
those extra registers.

Not having the perfomance counter registers isn't a problem, just replace
``perf_enable_counter(0);`` with
``printf("Entering loop at: %lu\n", perf_get_mcycle());`` and
``perf_disable_counter(0);`` with
``printf("Exiting loop at: %lu\n", perf_get_mcycle());``. ``perf_get_mcycle()``
returns the value of a free-running 32-bit counter. You'll just need to
manually write a script to parse the output and count how many cycles were
spent in the inner loop.

Looking at the total cycle count for ``CONV_2D`` and the cycle count in the
innermost loop, approximately 83% of our time in ``CONV_2D`` is spent in that
inner loop. Let's do some optimizations!

-------------------------------
Step 3: Software Specialization
-------------------------------

Before we write any hardware let's perform some simple, model-specific
optimizations in software. In order to understand what optimizations we can
make with our specific model, let's print out the parameters of the ``CONV_2D``
operation. Include "playground_util/print_params.h" and add the following to
the top of the function:

.. code-block:: C++

    #include "playground_util/print_params.h"
    /* ... */
    inline void ConvPerChannel(
        const ConvParams& params, const int32_t* output_multiplier,
        const int32_t* output_shift, const RuntimeShape& input_shape,
        const int8_t* input_data, const RuntimeShape& filter_shape,
        const int8_t* filter_data, const RuntimeShape& bias_shape,
        const int32_t* bias_data, const RuntimeShape& output_shape,
        int8_t* output_data) {
      // Format is:
      // "padding_type", "padding_width", "padding_height", "padding_width_offset",
      // "padding_height_offset", "stride_width", "stride_height",
      // "dilation_width_factor", "dilation_height_factor", "input_offset",
      // "weights_offset", "output_offset", "output_multiplier", "output_shift",
      // "quantized_activation_min", "quantized_activation_max",
      // "input_batches", "input_height", "input_width", "input_depth",
      // "filter_output_depth", "filter_height", "filter_width", "filter_input_depth",
      // "output_batches", "output_height", "output_width", "output_depth",
      print_conv_params(params, input_shape, filter_shape, output_shape);
      
      /* ... */

After running the golden tests again, we can observe the following parameters
are all constant:

======================  =====
Const. Parameter        Value
======================  =====
stride_width            1
stride_height           1
dilation_width_factor   1
dilation_height_factor  1
filter_height           1
filter_width            1
pad_width               0
pad_height              0
input_offset            128
======================  =====

By replacing all these parameters with literal values in the source code, we
get the following speedup in our golden tests:

::

     Counter |  Total | Starts | Average |     Raw
    ---------+--------+--------+---------+--------------
        0    |    72M | 124418  |   577   |     71859761
        1    |     0  |     0  |   n/a   |            0
        2    |     0  |     0  |   n/a   |            0
        3    |     0  |     0  |   n/a   |            0
        4    |     0  |     0  |   n/a   |            0
        5    |     0  |     0  |   n/a   |            0
        6    |     0  |     0  |   n/a   |            0
        7    |     0  |     0  |   n/a   |            0
       136M (   135730786) cycles total

Another optimization we can do is called "loop unrolling". Because
``input_depth`` is always a multiple of 4, we can make the innermost loop do
4 times as much work before checking the loop conditions. Implementing this
change should make your innermost loop look like:

.. code-block:: C++

    for (int in_channel = 0; in_channel < input_depth; in_channel += 4) {
      int32_t input_val = input_data[Offset(input_shape, batch, in_y,
                                              in_x, in_channel)];
      int32_t filter_val = filter_data[Offset(
          filter_shape, out_channel, filter_y, filter_x, in_channel)];
      acc += filter_val * (input_val + 128);
      
      input_val = input_data[Offset(input_shape, batch, in_y,
                                              in_x, in_channel + 1)];
      filter_val = filter_data[Offset(
          filter_shape, out_channel, filter_y, filter_x, in_channel + 1)];
      acc += filter_val * (input_val + 128);
  
      input_val = input_data[Offset(input_shape, batch, in_y,
                                              in_x, in_channel + 2)];
      filter_val = filter_data[Offset(
          filter_shape, out_channel, filter_y, filter_x, in_channel + 2)];
      acc += filter_val * (input_val + 128);
  
      input_val = input_data[Offset(input_shape, batch, in_y,
                                              in_x, in_channel + 3)];
      filter_val = filter_data[Offset(
          filter_shape, out_channel, filter_y, filter_x, in_channel + 3)];
      acc += filter_val * (input_val + 128);
    }

After this change we get another significant speed-up in our golden tests:

::
    
     Counter |  Total | Starts | Average |     Raw
    ---------+--------+--------+---------+--------------
        0    |    54M | 124418  |   431   |     53743879
        1    |     0  |     0  |   n/a   |            0
        2    |     0  |     0  |   n/a   |            0
        3    |     0  |     0  |   n/a   |            0
        4    |     0  |     0  |   n/a   |            0
        5    |     0  |     0  |   n/a   |            0
        6    |     0  |     0  |   n/a   |            0
        7    |     0  |     0  |   n/a   |            0
       117M (   117297894) cycles total

Even with the simplest possible software specialization, we've already seen
massive gains in performance. Our innermost loop is now twice as fast and
the total number of cycles spent in inference has decreased by 36%.

-----------------------------------
Step 4: Simple Calculation Gateware
-----------------------------------

Now that we've picked off some low-hanging fruit in our software, let's direct
our attention to our hardware.

In our innermost loop you might notice we load -- then multiply and
accumulate -- 8 different values from ``int8_t`` arrays. This is wasteful,
our registers are 32 bits wide and the ``int8_t`` values are already
contiguous in memory. With a custom CFU we could create a instruction that
performs a `SIMD <https://en.wikipedia.org/wiki/SIMD>`_
`multiply-and-accumulate 
<https://en.wikipedia.org/wiki/Multiply%E2%80%93accumulate_operation>`_
operation in one or two cycles.

The instruction will have two 32 bit inputs, a set of four bytes from
``input_data`` and a set of four bytes from ``filter_data``. Each time the
instruction is executed an internal register will accumulate and return the
running sum. We'll also need some way to reset the internal accumulator, we can
use the ``funct7`` field of the assembly instruction for this task. A non-zero
``funct7`` value will reset the internal accumulator to 0. A graphical
representation of the inputs and output of the instruction are shown below:

::

                  7 bits
             +--------------+
    funct7 = | (bool) reset |
             +--------------+

                  int8_t           int8_t           int8_t           int8_t
             +----------------+----------------+----------------+----------------+
       in0 = | input_data[0]  | input_data[1]  | input_data[2]  | input_data[3]  |
             +----------------+----------------+----------------+----------------+
   
                  int8_t           int8_t           int8_t           int8_t
             +----------------+----------------+----------------+----------------+
       in1 = | filter_data[0] | filter_data[1] | filter_data[2] | filter_data[3] |
             +----------------+----------------+----------------+----------------+
       
                                            int32_t
             +-------------------------------------------------------------------+
    output = | output + (input_data[0, 1, 2, 3] + 128) * filter_data[0, 1, 2, 3] |
             +-------------------------------------------------------------------+

Now that we've described our CFU it's time to actually write the gateware. If
you'd like to implement your CFU directly in Verilog you can skip the upcoming
section about Amaranth CFUs (and likewise if you're going to be using Amaranth you
can skip the Verilog section).

^^^^^^^^^^^^^^^^^^^^^^^^
Amaranth CFU Development
^^^^^^^^^^^^^^^^^^^^^^^^

There is a fairly robust framework for building a CFU in Amaranth. Inside of
``<CFU-Playground root>/python/amaranth_cfu`` there are a set of helper files
that you can ``import`` in your code. It's best to read through the doc
comments in ``<CFU-Playground root>/python/amaranth_cfu/cfu.py`` and
``<CFU-Playground root>/python/amaranth_cfu/util.py`` before starting
development, but you should be able to get a reasonable understanding of the
framework through this example.

.. code-block:: python

    from amaranth import C, Module, Signal, signed
    from amaranth_cfu import all_words, InstructionBase, InstructionTestBase, pack_vals, simple_cfu
    import unittest


    # Custom instruction inherits from the InstructionBase class.
    class SimdMac(InstructionBase):
        def __init__(self, input_offset=128) -> None:
            super().__init__()

            self.input_offset = C(input_offset, signed(9))

        # `elab` method implements the logic of the instruction.
        def elab(self, m: Module) -> None:
            words = lambda s: all_words(s, 8)

            # SIMD multiply step:
            self.prods = [Signal(signed(16)) for _ in range(4)]
            for prod, w0, w1 in zip(self.prods, words(self.in0), words(self.in1)):
                m.d.comb += prod.eq(
                    (w0.as_signed() + self.input_offset) * w1.as_signed())

            m.d.sync += self.done.eq(0)
            # self.start signal high for one cycle when instruction started.
            with m.If(self.start):
                with m.If(self.funct7):
                    m.d.sync += self.output.eq(0)
                with m.Else():
                    # Accumulate step:
                    m.d.sync += self.output.eq(self.output + sum(self.prods))
                # self.done signal indicates instruction is completed.
                m.d.sync += self.done.eq(1)


    # Tests for the instruction inherit from InstructionTestBase class.
    class SimdMacTest(InstructionTestBase):
        def create_dut(self):
            return SimdMac()

        def test(self):
            # self.verify method steps through expected inputs and outputs.
            self.verify([
                (1, 0, 0, 0),  # reset
                (0, pack_vals(-128, 0, 0, 1), pack_vals(111, 0, 0, 1), 129 * 1),
                (0, pack_vals(0, -128, 1, 0), pack_vals(0, 52, 1, 0), 129 * 2),
                (0, pack_vals(0, 1, 0, 0), pack_vals(0, 1, 0, 0), 129 * 3),
                (0, pack_vals(1, 0, 0, 0), pack_vals(1, 0, 0, 0), 129 * 4),
                (0, pack_vals(0, 0, 0, 0), pack_vals(0, 0, 0, 0), 129 * 4),
                (0, pack_vals(0, 0, 0, 0), pack_vals(-5, 0, 0, 0), 0xffffff84),
                (1, 0, 0, 0),  # reset
                (0, pack_vals(-12, -128, -88, -128), pack_vals(-1, -7, -16,
                                                               15), 0xfffffd0c),
                (1, 0, 0, 0),  # reset
                (0, pack_vals(127, 127, 127, 127), pack_vals(127, 127, 127,
                                                             127), 129540),
                (1, 0, 0, 0),  # reset
                (0, pack_vals(127, 127, 127,
                              127), pack_vals(-128, -128, -128, -128), 0xfffe0200),
            ])


    # Expose make_cfu function for cfu_gen.py
    def make_cfu():
        # Associate cfu_op0 with SimdMac.
        return simple_cfu({0: SimdMac()})


    # Use `../../scripts/pyrun cfu.py` to run unit tests.
    if __name__ == '__main__':
        unittest.main()

This CFU implements our instruction specification whilst being easily testable
and extendable.

^^^^^^^^^^^^^^^^^^^^^^^
Verilog CFU Development
^^^^^^^^^^^^^^^^^^^^^^^

Developing CFUs in Verilog is lower-level and doesn't give you access to the nice
testing features of Amaranth, but it does give you more control over the CFU. 
Firstly, delete the ``cfu.py`` and ``cfu_gen.py``
files from your project folder; we'll directly be creating and editing a file
named ``cfu.v``.   To add the ``cfu.v`` file in ``git``, you'll need to use the 
force option: ``git add -f cfu.v``.

When doing CFU development with Amaranth, the CFU-CPU handshaking is implemented
for you in the ``Cfu`` base class. In Verilog you will need to implement your
own handshaking and for that it's important to know the CFU module
specification.

The “CFU bus” provides communication between the CPU and CFU.
The CFU Bus is composed of two independent streams:

- The CPU uses the command stream (cmd) to send operands and 10 bits of
  function code to the CFU, thus initiating the CFU computation.

- The CFU uses the response stream (rsp) to return the result to the CPU. Since
  the responses are not tagged, they must be delivered in-order.

Each stream has two-way handshaking and backpressure (``*_valid`` and
``*_ready`` in the diagram below). An endpoint can indicate that it cannot
accept another transfer by pulling its ``ready`` signal low. A transfer takes
place only when both ``valid`` from the sender and ``ready`` from the receiver
are high.

.. note:: The data values from the CPU (``cmd_function_id``, ``cmd_inputs_0``, 
          and ``cmd_inputs_1``) are valid ONLY during the cycle that the
          handshake is active (when both ``cmd_valid`` and ``cmd_ready`` are
          asserted).   If your CFU needs to use these values in subsequent 
          cycles, it must store them in registers.


::

        >--- cmd_valid --------------->
        <--- cmd_ready ---------------<
        >--- cmd_function_id[9:0] ---->
        >--- cmd_inputs_0[31:0] ------>
        >--- cmd_inputs_1[31:0] ------>
    CPU                                 CFU
        <--- rsp_valid ---------------<
        >--- rsp_ready --------------->
        <--- rsp_outputs_0[31:0] -----<

With the previous specification in mind, here's an implementation of our
SIMD multiply-and-accumulate instruction in ``cfu.v``:

.. code-block:: Verilog

    module Cfu (
      input               cmd_valid,
      output              cmd_ready,
      input      [9:0]    cmd_payload_function_id,
      input      [31:0]   cmd_payload_inputs_0,
      input      [31:0]   cmd_payload_inputs_1,
      output reg          rsp_valid,
      input               rsp_ready,
      output reg [31:0]   rsp_payload_outputs_0,
      input               reset,
      input               clk
    );
      localparam InputOffset = $signed(9'd128);
    
      // SIMD multiply step:
      wire signed [15:0] prod_0, prod_1, prod_2, prod_3;
      assign prod_0 =  ($signed(cmd_payload_inputs_0[7 : 0]) + InputOffset)
                      * $signed(cmd_payload_inputs_1[7 : 0]);
      assign prod_1 =  ($signed(cmd_payload_inputs_0[15: 8]) + InputOffset)
                      * $signed(cmd_payload_inputs_1[15: 8]);
      assign prod_2 =  ($signed(cmd_payload_inputs_0[23:16]) + InputOffset)
                      * $signed(cmd_payload_inputs_1[23:16]);
      assign prod_3 =  ($signed(cmd_payload_inputs_0[31:24]) + InputOffset)
                      * $signed(cmd_payload_inputs_1[31:24]);
    
      wire signed [31:0] sum_prods;
      assign sum_prods = prod_0 + prod_1 + prod_2 + prod_3;
    
      // Only not ready for a command when we have a response.
      assign cmd_ready = ~rsp_valid;
    
      always @(posedge clk) begin
        if (reset) begin
          rsp_payload_outputs_0 <= 32'b0;
          rsp_valid <= 1'b0;
        end else if (rsp_valid) begin
          // Waiting to hand off response to CPU.
          rsp_valid <= ~rsp_ready;
        end else if (cmd_valid) begin
          rsp_valid <= 1'b1;
          // Accumulate step:
          rsp_payload_outputs_0 <= |cmd_payload_function_id[9:3]
              ? 32'b0
              : rsp_payload_outputs_0 + sum_prods;
        end
      end
    endmodule

^^^^^^^^^^^^^^^^^^^^^^^^^
Using the CFU in Software
^^^^^^^^^^^^^^^^^^^^^^^^^

No matter what language you chose to write your CFU in, it won't be very
useful if you don't use it in your software!

In your project-specific conv.h file, modify the loops to utilize your CFU
SIMD multiply-and-accumulate instruction:

.. code-block:: C++

    #include "cfu.h"
    /* ... */
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          int32_t acc = cfu_op0(/* funct7= */ 1, 0, 0); // resets acc
          for (int filter_y = 0; filter_y < 1; ++filter_y) {
            const int in_y = in_y_origin + filter_y;
            for (int filter_x = 0; filter_x < 1; ++filter_x) {
              const int in_x = in_x_origin + filter_x;
               
              // Zero padding by omitting the areas outside the image.
              const bool is_point_inside_image =
                  (in_x >= 0) && (in_x < input_width) && (in_y >= 0) &&
                  (in_y < input_height);
                 
              if (!is_point_inside_image) {
                continue;
              }
               
              for (int in_channel = 0; in_channel < input_depth; in_channel += 4) {
                uint32_t input_val = *((uint32_t *)(input_data + Offset(
                    input_shape, batch, in_y, in_x, in_channel)));
                      
                uint32_t filter_val = *((uint32_t *)(filter_data + Offset(
                    filter_shape, out_channel, filter_y, filter_x, in_channel)));
                acc = cfu_op0(/* funct7= */ 0, /* in0= */ input_val, /* in1= */ filter_val);
              }
            }
          }
             
          if (bias_data) {
            acc += bias_data[out_channel];
          }
          acc = MultiplyByQuantizedMultiplier(
              acc, output_multiplier[out_channel], output_shift[out_channel]);
          acc += output_offset;
          acc = std::max(acc, output_activation_min);
          acc = std::min(acc, output_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, out_channel)] =
              static_cast<int8_t>(acc);
        }
    /* ... */

After modifying this code, re-build the project and bitstream to test out the
changes. When running the golden tests you should first make sure they all
pass and then note the cycle count.

::

     Counter |  Total | Starts | Average |     Raw
    ---------+--------+--------+---------+--------------
        0    |    22M | 124418  |   178   |     22147970
        1    |     0  |     0  |   n/a   |            0
        2    |     0  |     0  |   n/a   |            0
        3    |     0  |     0  |   n/a   |            0
        4    |     0  |     0  |   n/a   |            0
        5    |     0  |     0  |   n/a   |            0
        6    |     0  |     0  |   n/a   |            0
        7    |     0  |     0  |   n/a   |            0
        86M (    85771518) cycles total

What an improvement! Compared to the unoptimized version, the innermost loop is
five times faster and the total number of cycles spent in inference has
decreased by 47%. 

For extra analysis you can look at the ``build`` folder in your project
directory. In there you can inspect disassemblies of your software to see how
the addition of your CFU improved the code.

Before adding the CFU this is what the assembly of our innermost loop looked
like:

.. code-block:: asm

    # innermost loop before adding CFU
    lw      a4,16(sp)
    blez    a4,4005f0dc
    lw      a4,24(sp)
    add     a0,a4,a3
    lw      a4,28(sp)
    add     a2,a4,a2
    lw      a4,36(sp)
    add     a3,a4,a3
    mv      t5,a3
    lb      a4,0(a0)
    lb      t0,0(a2)
    lb      a3,1(a2)
    addi    a4,a4,128
    mul     a4,a4,t0
    sw      a3,4(sp)
    lb      a3,2(a2)
    lb      t4,1(a0)
    lb      t3,2(a0)
    sw      a3,8(sp)
    lw      t0,4(sp)
    lb      a3,3(a0)
    lb      s4,3(a2)
    addi    t4,t4,128
    add     a4,a4,a5
    lw      a5,8(sp)
    addi    t3,t3,128
    mul     t4,t4,t0
    addi    a3,a3,128
    addi    a0,a0,4
    addi    a2,a2,4
    mul     t3,t3,a5
    add     t4,a4,t4
    mul     a3,a3,s4
    add     a5,t4,t3
    add     a5,a5,a3
    bne     t5,a0,4005f218


After adding the CFU, the assembly has greatly shrunk in size as our CFU does
the heavy lifting:

.. code-block:: asm

    # innermost loop after adding CFU
    lw        a7,4(sp)
    blez      a7,4005f0dc
    lw        a0,12(sp)
    add       a7,a0,a5
    lw        a0,16(sp)
    add       a4,a0,a4
    lw        a0,24(sp)
    add       a5,a0,a5
    lw        a0,0(a7)
    lw        t1,0(a4)
    cfu[0,0]  a0, a0, t1
    addi      a7,a7,4
    addi      a4,a4,4
    bne       a5,a7,4005f200

With just simple software improvements and a tiny CFU we've decreased the
number of cycles taken by the innermost loop from 113 million down to just
22 million!

------------------
Step 5: Next Steps
------------------

This document only briefly touched on very simple hardware and software
optimizations, but there's so much more that can be done. Possible next steps
include:

- `Stronger software optimization
  <https://en.wikipedia.org/wiki/Optimizing_compiler#Specific_techniques>`_
- Moving entire loops from software to gateware
- Optimization of other TensorFlow operations
- Investigation of other models
- Generalizing instructions so they can be used in multiple places
