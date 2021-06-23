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


Step 2: Install Vivado and renode
---------------------------------

1. vivaldo

  (can take ~8 hours to download software)
  See https://cfu-playground.readthedocs.io/en/latest/vivado-install.html for a comprehensive guide.

2. renode

   Either "apt-get install renode" or get renode-xxx-linux.portable.tar.gz from
   https://dl.antmicro.com/projects/renode/builds/ (and make sure renode is in your PATH)


Step 3: Install RISCV toolchain
-------------------------------

1. Download the `April 2020`_ toolchain from freedom-tools and unpack the binaries to a directory:

.. _`April 2020`: https://github.com/sifive/freedom-tools/releases/tag/v2020.04.0-Toolchain.Only

.. code-block:: bash

   $ mkdir ~/bin
   $ cd ~/bin
   $ tar xvfz ~/Downloads/riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14.tar.gz


2. Add the RISCV_DIR environment variable to your ``.bashrc`` script:

.. code-block:: bash

   RISCV_DIR=/home/<your name>/bin/riscv64-unknown-elf-gcc-8.3.0-2020.04.1-x86_64-linux-ubuntu14/bin



Step 4: Clone the CFU-Playground Repository
-------------------------------------------

Clone the repository from the github:

.. code-block:: bash

   git clone https://github.com/google/CFU-Playground.git


Step 5: Setup python virtual environment + setup
------------------------------------------------

Python virtualenv ensures that you have the correct python and modules needed by this code.

.. code-block:: bash

   $ virtualenv CFU-Playground
   $ cd CFU-Playground
   $ source bin/activate   # start python3 virtualenv
   $ pip install --upgrade 'git+https://github.com/nmigen/nmigen.git#egg=nmigen[builtin-yosys]'
   $ # Check that you have the correct gcc in path
   $ (CFU-Playground) sauron:~/fpga/CFU-Playground$ type riscv64-unknown-elf-gcc; riscv64-unknown-elf-gcc --version |head -1
   riscv64-unknown-elf-gcc is hashed (/home/merlin/fpga/riscv64-unknown-elf-gcc/bin/riscv64-unknown-elf-gcc)
   riscv64-unknown-elf-gcc (SiFive GCC 8.3.0-2020.04.1) 8.3.0
   $ scripts/setup         # install prerequisites
   
Step 6: Test Run
----------------

Test that everything is working by building the template project. The template
project is designed to be used a base for your own projects, and it also serves
as a useful "minimal" system.

.. code-block:: bash

   # Go to the proj_template directory
   $ cd proj/proj_template

   # Start from an empty build
   $ make clean

   # Program the bitstream onto the board. The first run will take several minutes
   # as Vivado synthesizes a bitstream
   # If this works fine, you will get a chasing LED pattern with the 4 LEDs
   $ make prog

   # Build the RISCV program and load it onto the board
   # Also starts a terminal ( exit the terminal with CTRL+\ )
   $ make load
   (...)
   /home/merlin/fpga/CFU-Playground/soc/bin/litex_term --speed 3686400  --kernel /home/merlin/fpga/CFU-Playground/proj/proj_template/build/software.bin /dev/ttyUSB1
   (nothing happens, type ENTER)
   litex> reboot <- type this or push reset button on board
   --============== Boot ==================--
   Booting from serial...
   Press Q or ESC to abort boot completely.
   sL5DdSMmkekro
   [LXTERM] Received firmware download request from the device.
   [LXTERM] Uploading /home/merlin/fpga/CFU-Playground/proj/proj_template/build/software.bin to 0x40000000 (879876 bytes)...
   [LXTERM] Upload complete (317.9KB/s).
   [LXTERM] Booting the device.
   [LXTERM] Done.
   Executing booted program at 0x40000000
   
   --============= Liftoff! ===============--
   Hello, World!
   initTfLite()
   
   CFU Playground
   ==============
   1: TfLM Models menu
   2: Functional CFU Tests
   3: Project menu
   4: Performance Counter Tests
   5: TFLite Unit Tests
   6: Benchmarks
   7: Util Tests
   main> 


* Select `1` - TfLM Models menu
* Then `1` - Person Detection int8 model
* Then `g` - Golden tests

If the golden tests pass, then all is well.
