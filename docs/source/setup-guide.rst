Setup Guide
============

This is a guide to setting up to use the CFU-Playground.


Step 1: Acquire an Arty A7-35T or other supported board
---------------------------------------------------------

The Arty A7-35T is available from several distributors, including direct from
the `Digilent Store`_, `Element 14`_ or `Mouser`_. The A7-100T will also work,
but is significantly more expensive.

.. _`Digilent Store`: https://store.digilentinc.com/arty-a7-artix-7-fpga-development-board/
.. _`Element 14`: https://au.element14.com/avnet/aes-a7mb-7a35t-g/eval-board-arty-artix-7-low-cost/dp/277520502?st=arty%20a7
.. _`Mouser`: https://au.mouser.com/ProductDetail/Digilent/410-319?qs=%2Fha2pyFaduiP6GD6DfdhNp6rR4rT1KTVOohSnRQ%252BMgra5hr4M7aEiQ%3D%3D


Other options that have been tested:

* iCEBreaker by 1BitSquared
* OrangeCrab by GSD
* ULX3S by Radiona
* FOMU by Kosagi
* Nexys Video by Digilent


Step 2: Clone the CFU-Playground Repository
-------------------------------------------

Clone the repository from the github:

.. code-block:: bash

   git clone https://github.com/google/CFU-Playground.git


Step 3: Run the setup script
-------------------------------------------

This updates submodules, builds some local executables, and installs missing Linux packages.

.. code-block:: bash

   cd CFU-Playground
   ./scripts/setup

If you intend to use Amaranth to build CFUs, you may need a compatible version of Yosys,
which can be installed with:

.. code-block:: bash

 pip3 install amaranth-yosys

Step 4: Install Toolchain
--------------------------------------------

There are a few options depending on whether your board has a Xilinx FPGA
or not, and whether you want to use Conda or not.  If you have already installed
a toolchain and can build bitstreams for your board, you probably
don't need to do anything.


Option 4a: Install Conda package for SymbiFlow (for Xilinx)
--------------------------------------------------------------

To download and install the open source SymbiFlow tools and databases,
run the following from the top directory of the CFU Playground.
It will take about six minutes in the best case,
and use approximately 25GB of disk space.
You normally only need to do this once.

.. code-block:: bash

   make install-sf

Then, each time to enter the environment, type:

.. code-block:: bash

   make enter-sf

This starts a subshell; you can leave the environment by typing ``exit``.

Later when you're building a project bitstream,
you need to add USE\_SYMBIFLOW=1 to your make command line.

If you see no errors, but the compiled RISC-V executable does not run on the
board, you may need to lower the target clock rate.
This can be done by adding ``EXTRA_LITEX_ARGS="--sys-clk-freq {clockrate}"``
to the make command, where {clockrate} if the desired clock rate in Hz.
This will be required if you are using the suggested Arty A7 for the test run
in Step 6 (try ``75000000`` Hz).


Option 4b: Install Conda packages for Lattice FPGAs
-----------------------------------------------------

This installs yosys and nextpnr versions and all other support tools
for building bitstreams for Lattice iCE40, ECP5, and CrossLink/Nexus FPGAs.
You normally only need to do this once.

.. code-block:: bash

   make env

Then, each time to enter the environment, type:

.. code-block:: bash

   make enter

This starts a subshell; you can leave the environment by typing ``exit``.



Option 4c: Use already-installed Yosys, Nextpnr, and other required tools
--------------------------------------------------------------------------

This option makes sense if you have already installed the necessary open-source
tools for your board.   In that case you don't need to do anything other than
make sure that they're in your PATH.



Option 4d: Install/Use Vivado
----------------------------------

If you are using a board with a Xilinx part, such as Arty A7 or Nexys Video,
and you **don't** want to use open source SymbiFlow tools, then install
Vivado if it is not already installed on your system.

See https://cfu-playground.readthedocs.io/en/latest/vivado-install.html for
a comprehensive guide. Note that the software can take up to **8 hours** to
download, so plan to do that ahead of time.

You will need to source the settings64.sh script each time you start a shell,
or do it in your .bashrc.



Step 5: Install RISC-V toolchain
---------------------------------

.. note::

   This is only required if you don't use one of the Conda options above.
   All of the Conda packages include the RISC-V toolchain.

1. Download the `August 2020`_ toolchain from freedom-tools and unpack the binaries to your home directory:

.. _`August 2020`: https://github.com/sifive/freedom-tools/releases/tag/v2020.08.0

.. code-block:: bash

   $ tar xvfz ~/Downloads/riscv64-unknown-elf-gcc-10.1.0-2020.08.2-x86_64-linux-ubuntu14.tar.gz

2. Add the toolchain to your `PATH` in your ``.bashrc`` script:

.. code-block:: bash

   export PATH=$PATH:$HOME/riscv64-unknown-elf-gcc-10.1.0-2020.08.2-x86_64-linux-ubuntu14/bin


Step 6: Test Run
----------------

Test that everything is working by building the template project. The template
project is designed to be used a base for your own projects, and it also serves
as a useful "minimal" system.

The following assumes the default Arty A7-35T.   If you use a different board, add ``TARGET=board``
to each of the ``make`` commands.   For example, to target iCEBreaker, add ``TARGET=icebreaker``.

.. code-block:: bash

   # If using Symbiflow (option 4a)
   $ make enter-sf

   # Go to the proj_template directory
   $ cd proj/proj_template

   # Start from an empty build
   $ make clean

   # Program the bitstream onto the board. The first run will take several minutes
   # as the bitstream is synthesized.
   # Set TARGET and USE_* flags to match your installation.
   $ make prog TARGET=digilent_arty USE_SYMBIFLOW=1
   #  OR
   $ make prog TARGET=digilent_arty USE_VIVADO=1

   # If this works fine, you will get a chasing LED pattern with the 4 LEDs

   # Build the RISCV program and load it onto the board
   # Also starts a terminal ( exit the terminal by hitting CTRL+C twice rapidly )
   # Set TARGET to match your board
   # Set BUILD_JOBS to match the number of CPUs available on your system
   $ make load BUILD_JOBS=4 TARGET=digilent_arty
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

If the golden tests pass, then all is well (remember that you can exit with CTRL+C)
