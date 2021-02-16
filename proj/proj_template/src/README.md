# Source Overlay directory

The files in this directory will be "overlaid" on a copy of the common source tree and Tensorflow Lite for Microcontrollers. 

This means:

    * the main.c file in this directory replaces the main.c file in common.
    * to replace the integer 2D convolution implementation, you could
      create a file with the path:

    tensorflow/lite/kernels/interal/reference/integer_ops/conv.h.

    