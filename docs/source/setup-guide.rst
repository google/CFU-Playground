Setup Guide
===========

This is a guide to setting up to use the CFU-Playground.


Step 1: Order an Arty A7-35T
----------------------------

(allow 1-2 week delivery time)

The Arty A7-35T is available from several distributors, including direct from
the `Digilent Store`_, `Element 14`_ or `Mouser`_. The A7-100T will also work,
but is significantly more expensive.

.. _`Digilent Store`: https://store.digilentinc.com/arty-a7-artix-7-fpga-development-board/
.. _`Element 14`: https://au.element14.com/avnet/aes-a7mb-7a35t-g/eval-board-arty-artix-7-low-cost/dp/277520502?st=arty%20a7
.. _`Mouser`: https://au.mouser.com/ProductDetail/Digilent/410-319?qs=%2Fha2pyFaduiP6GD6DfdhNp6rR4rT1KTVOohSnRQ%252BMgra5hr4M7aEiQ%3D%3D 


Step 2: Install Vivado
----------------------

(can take ~8 hours to download software)

See :doc:vivado-install for a comprehensive guide.


Step 3: Install RISCV toolchain
-------------------------------

1. Download the `April 2020`_ toolchain from freedom-tools.

.. _`April 2020`: https://github.com/sifive/freedom-tools/releases/tag/v2020.04.0-Toolchain.Only

2. Unpack the binaries to a directory:

.. code-block:: bash

   $ mkdir ~/bin
   $ cd ~/bin
   $ tar xvfz ~/Downloads/riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14.tar.gz

3. Add the RISCV_DIR environment variable to your ``.bashrc`` script:

.. code-block:: bash

   RISCV_DIR=/home/<your name>/bin/riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14/bin


Step 4: Clone the CFU-Playground Repository
-------------------------------------------

Clone the repository from the github:

.. code-block:: bash

   git clone https://github.com/google/CFU-Playground.git


Step 5: Run Setup
-----------------

The setup script ensures that all git submodules are updated and that required
software is installed:

.. code-block:: bash

   $ cd CFU-Playground
   $ scripts/setup


Step 6: Test Run
----------------

Test that everything is working by building the template project. The template
project is designed to be used a base for your own projects, and it also serves
as a useful "minimal" system.

.. code-block:: bash

   # Go to the proj_template directory
   $ cd CFU-Playground
   $ cd proj/proj_template

   # Start from an empty build
   $ make clean

   # Program the bitstream onto the board. The first run will take several minutes
   # as Vivado synthesizes a bitstream
   $ make prog

   # Build the RISCV program and load it onto the board
   # Also starts a terminal
   $ make load

This will start a terminal and display a menu.

* Select `1` - TfLM Models menu
* Then `1` - Person Detection int8 model
* Then `g` - Golden tests

If the golden tests pass, then all is well.
