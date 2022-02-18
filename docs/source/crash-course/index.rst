==========================
Crash Course on Everything
==========================

This page provides a high-level overview of what you need to know in order to 
accelerate ML models with the CFU Playground. 

Hint: Broad knowledge over the whole stack is more useful than deep knowledge 
of any one part. Although each of these topics is very interesting in itself, it
is better to learn the basics for each area and start applying them, and later
work out where the gaps in your knowledge may be.

* Tensorflow Lite for Microcontrollers 
* RISCV and CFUs
* Writing gateware with Verilog and Amaranth
* LiteX and SoCs.
* Getting help.


Required Background Knowledge
=============================

We assume you have some knowledge of:

C and C++ for Microcontrollers
    C_ and `C++`_ are the languages used in for programming microcontrollers in the
    CFU Playground, and you will need a basic understanding of these languages.

    We recommend playing with Arduino_ as an excellent way to learn how to
    program microcontrollers with C and C++.

    Advanced understanding is not needed, since you'll be reading and modifying
    a lot more code than you'll be writing.

Python
    The Amaranth framework uses Python_. It is remarkably easy to learn the
    basics of Python. If you have a couple of days, we recommend working
    through chapters 0 to 11 of `Dive Into Python 3`_. Dive Into Python 3 is
    well paced and provides many practical exercises.

.. _`C`: https://en.wikipedia.org/wiki/C_(programming_language)
.. _`C++`: https://en.wikipedia.org/wiki/C%2B%2B
.. _Arduino: https://arduino.cc
.. _Python: https://python.org
.. _`Dive Into Python 3`: https://diveintopython3.problemsolving.io/

It is also helpful to have some knowledge of:

General Linux fu
    Including GNU make and general bash scripting.

Git
    How to make branches and commits, fork a github respository and submit PRs.

The Crash Course
================

:doc:`tflm`
    The technology we use for evaluating ML models, and the accelerators in the
    CFU-Playground fit into this model.

:doc:`gateware`
    At the lowest level, accelerators are built from gateware, and you'll need
    to know how to write Verilog and/or Amaranth_.

:doc:`litex`
    LiteX is a framework for defining FPGA SoCs. CFU-Playground accelerators
    work inside a LiteX SoC.

:doc:`riscv`
    The CFU-Playground accelerators are implemented as Custom Function Units
    for a RISCV CPU.

:doc:`getting-help`
    Building accelerators is hard. It is essential to know how to ask for help.

.. _Amaranth: https://github.com/amaranth-lang/amaranth


Index
=====

.. toctree::
   :maxdepth: 2

   tflm
   gateware
   litex
   riscv
   getting-help


