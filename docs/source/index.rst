.. CFU-Playground documentation master file, created by
   sphinx-quickstart on Tue Mar  9 18:35:27 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The CFU Playground: Accelerate ML models on FPGAs
=================================================

"CFU" stands for Custom Function Unit: accelerator hardware that is tightly
coupled into the pipeline of a CPU core, to add new custom function
instructions that complement the CPU’s standard functions (such as
arithmetic/logic operations).

The CFU Playground is a collection of software, gateware and hardware
configured to make it easy to:

* Run ML models

* Benchmark and profile performance

* Make incremental improvements

  * In software by modifying source code

  * In gateware with a CFU

* Measure the results of changes

ML acceleration on microcontroller-class hardware is a new area, and one that, due
to the expense of building ASICs, is currently dominated by hardware engineers.
In order to encourage software engineers to join in the innovation, the
CFU-Playground aims to make experimentation as simple, fast and fun as
possible.

As well as being a useful tool for accelerating ML inferencing, the CFU Playground is
a relatively gentle introduction to using FPGAs for computation.

If you find that you need help or that anything is not working as you expect,
please `raise an issue`_ and we'll do our best to point you in the right direction.

.. _`raise an issue`: https://github.com/google/CFU-Playground/issues/new


**Disclaimer: This is not an officially supported Google project. Support and/or new releases may be limited.**


Learning and Using the CFU Playground
-------------------------------------

Begin with the :doc:`overview`, which explains the various hardware, software and
gateware components that make up the CFU Playground.

:doc:`setup-guide` gives detailed instructions for setting up an environment.

:doc:`crash-course/index` explains the basics of FPGAs, Verilog, `Amaranth`_,
RISCV, Custom Function Units and `Tensorflow Lite for Microcontrollers`_.

:doc:`step-by-step` will guide you through creating your first accelerator.

:doc:`renode` can tell you more about simulating your project in `Renode`_.

.. _`Tensorflow Lite for Microcontrollers`: https://www.tensorflow.org/lite/microcontrollers
.. _Amaranth: https://github.com/amaranth-lang/amaranth
.. _Renode: https://renode.io

.. raw:: html

   <img class="std"
       alt="Overview showing hardware, gateware and software layers"
       src="https://docs.google.com/drawings/d/e/2PACX-1vS_ydCYGB6yykkh3EXcmcv48NoC-o7ywYXUxiP8kzuFNfpQm-0K8cK73pgb3VqOCs0vPhtsPaX1Nvot/pub?w=958&amp;h=726">


Site Index
==========

.. toctree::
   :maxdepth: 2
   :glob:

   overview
   setup-guide
   crash-course/index
   step-by-step
   interface
   renode
   vivado-install
   docs/index
   projects/*


.. Not currently in use
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`
