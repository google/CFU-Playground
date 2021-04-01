.. CFU-Playground documentation master file, created by
   sphinx-quickstart on Tue Mar  9 18:35:27 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The CFU Playground
==================

Accelerate Tensorflow Lite for Microcontrollers on FPGAs.

What It Is
----------

The CFU Playground provides tools and infrastructure for programmers building 
hardware ML inferencing accelerators. 

It brings together a C++ build environment, a collection of ML models, 
`Tensorflow Lite for Microcontrollers`_ , an FPGA toolchain and profiling tools
in way that allows a developer to incrementally design and build accelerators.

.. ditaa::

   +--------+   +-------+    +-------+
   |        | --+ ditaa +--> |       |
   |  Text  |   +-------+    |diagram|
   |Document|   |!magic!|    |       |
   |     {d}|   |       |    |       |
   +---+----+   +-------+    +-------+
       :                         ^
       |       Lots of work      |
       +-------------------------+

_`Tensorflow Lite for Microcontrollers`: https://www.tensorflow.org/lite/microcontrollers


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   docs/index
   



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
