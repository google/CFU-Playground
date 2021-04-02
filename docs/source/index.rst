.. CFU-Playground documentation master file, created by
   sphinx-quickstart on Tue Mar  9 18:35:27 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The CFU Playground: Accelerate ML models on FPGAs
=================================================

The CFU Playground is a collection of software, gateware and hardware configured to 
make it easy to:

* "Run" ML models 
* Benchmark and profile performance 
* Make incremental improvements
* Measure the results of changes

As well as being a useful tool for accelerating ML inferencing, the CFU Playground is 
a relatively gentle introduction to using FPGAs for computation.

Learning and Using the CFU Playground
-------------------------------------

Begin with the :doc:`overview`, which explains the various hardware, software and gateware components that make up the CFU Playground.

:doc:`crash-course` explains the basics of FPGAs, Verilog, nMigen, RISCV, Custom Function Units and `Tensorflow Lite for Microcontrollers`_. 

:doc:`step-by-step` will guide you through creating your first accelerator.

.. _`Tensorflow Lite for Microcontrollers`: https://www.tensorflow.org/lite/microcontrollers

.. image:: images/overview.svg
   :height: 400px
   :align: center
   :alt: Overview showing hardware, gateware and software layers


Site Index
==========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   crash-course
   step-by-step
   docs/index
   

.. Not currently in use
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`
