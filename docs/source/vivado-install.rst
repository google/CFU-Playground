Vivado HLS WebPack Installation
===============================

This page is a guide on installing `Vivado HL WebPack`_ on Linux.

.. _`Vivado HL WebPack`: https://www.xilinx.com/products/design-tools/vivado/vivado-webpack.html

Vivado HL is Xilinx' FPGA toolchain. It can work with either Verilog or VHDL.
It is a large toolchain, and we only use a small fraction of its
capabilities. WebPack is the free version of Vivado.

You will need to create an account on the Xilinx website in order to use
Vivado.

A new versions of Vivado is released every 6 months or so. Version 2020.1 is
known to work. Newer versions are also likely to work, however we recommend
using 2020.1 unless you come across a reason not to.


Supported OS
------------

Check whether your OS is supported by looking at Chapter 2 of the
Vivado User Guide UG973_. If it is supported, then do a
`Standard GUI Installation`_. Otherwise, use the `Manual Installation`_.

.. _UG973: https://www.xilinx.com/support/documentation/sw_manuals/xilinx2020_1/ug973-vivado-release-notes-install-license.pdf


Standard GUI Installation
-------------------------

From the `2020.1 Download`_ page:

1. Scroll down to "Vivado Design Suite - HLx Editions - 2020.1  Full Product
   Installation".
2. Download the "Linux Self Extracting Web Installer" to, say, the
   ``~/Downloads`` folder. If you are not already logged into the Xilinx site,
   you will now need to create an account and log in.
3. Run the installer:

.. code-block:: bash

   $ cd ~/Downloads
   $ chmod +x Xilinx_Unified_2020.1_0602_1208_Lin64.bin
   $ ./Xilinx_Unified_2020.1_0602_1208_Lin64.bin

If your operating system is not supported you may get an error such as ``Exception in thread
"SPLASH_LOAD_MESSAGE"``. In that case, try the `Manual Installation`_.

.. _`2020.1 Download`: https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools/2020-1.html

**Important**: Add the main Vivado binary directory to your `PATH`, by adding
something like this to your .bashrc:

.. code-block:: bash

   export PATH=/home/<your name>/tools/Xilinx/Vivado/2020.1/bin:$PATH

Manual Installation
-------------------

From the `2020.1 Download`_ page:

* Step 1: Scroll down to "Vivado Design Suite - HLx Editions - 2020.1  Full Product
  Installation".
* Step 2: Download the "All OS installer Single-File Download" (35GB). If you are not
  already logged into the Xilinx site, you will now need to create an account
  and log in.
* Step 3: Untar the downloaded file and run xssetup:

.. code-block:: bash

   $ tar xvzf Xilinx_Unified_2020.1_0602_1208.tar.gz
   $ cd Xilinx_Unified_2020.1_0602_1208

   # Enter the email address and password for your xilinx.com account
   $ ./xsetup -b AuthTokenGen

   # This will create configuration file
   $ ./xsetup -b ConfigGen
   # Choose 2. Vivado, then
   # Choose 1. Vivado HL WebPACK

*  Step 4: Edit the created configuration file. Pay particular attention to
   the **Destination** directory path and the **Modules** list

.. code-block::

   #### Vivado HL WebPACK Install Configuration ####
   Edition=Vivado HL WebPACK

   Product=Vivado

   # Path where Xilinx software will be installed.
   Destination=/home/<your user>/tools/Xilinx

   # Choose the Products/Devices the you would like to install.
   Modules=Virtex UltraScale+ HBM:0,Zynq UltraScale+ MPSoC:0,DocNav:1,Kintex UltraScale:0,Zynq-7000:0,Spartan-7:0,System Generator for DSP:0,Artix-7:1,Virtex UltraScale+:0,Kintex-7:0,Kintex UltraScale+:0,Model Composer:0

   # Choose the post install scripts you'd like to run as part of the finalization step. Please note that some of these scripts may require user interaction during runtime.
   InstallOptions=

   ## Shortcuts and File associations ##
   # Choose whether Start menu/Application menu shortcuts will be created or not.
   CreateProgramGroupShortcuts=1

   # Choose the name of the Start menu/Application menu shortcut. This setting will be ignored if you choose NOT to create shortcuts.
   ProgramGroupFolder=Xilinx Design Tools

   # Choose whether shortcuts will be created for All users or just the Current user. Shortcuts can be created for all users only if you run the installer as administrator.
   CreateShortcutsForAllUsers=0

   # Choose whether shortcuts will be created on the desktop or not.
   CreateDesktopShortcuts=1

   # Choose whether file associations will be created or not.
   CreateFileAssociation=1

   # Choose whether disk usage will be optimized (reduced) after installation
   EnableDiskUsageOptimization=1

* Step 5: run the installation.

.. code-block:: bash

   $ ./xsetup -b Install -c ~/.Xilinx/install_config.txt -a XilinxEULA,3rdPartyEULA,WebTalkTerms

* Step 6: install drivers

.. code-block:: bash

   $ cd tools/Xilinx/Vivado/2020.1/data/xicom/cable_drivers/lin64/install_script/install_drivers
   $ sudo ./install_drivers

* Step 7: Add the main Vivado binary directory to your `PATH`, putting this in
  your `.bashrc` file:

.. code-block:: bash

   export PATH=/home/<your name>/tools/Xilinx/Vivado/2020.1/bin:$PATH


* Step 8: Enjoy of beverage of your choice. You deserve it. Congrats on getting Vivado installed!



Troubleshooting Vivado
----------------------

libtinfo.so.5
`````````````

If you encounter *application-specific initialization failed: couldn't load file "librdi_commontasks.so": libtinfo.so.5: cannot open shared object file: No such file or directory*,
try:

.. code-block:: bash

   $ sudo apt update
   $ sudo apt install libtinfo-dev
   $ sudo ln -s /lib/x86_64-linux-gnu/libtinfo.so.6 /lib/x86_64-linux-gnu/libtinfo.so.5


Hardware Manager Can't find the Arty A7
```````````````````````````````````````

If your hardware manager isn't seeing your device, try installing the drivers again:

.. code-block:: bash

   $ cd tools/Xilinx/Vivado/2020.1/data/xicom/cable_drivers/lin64/install_script/install_drivers
   $ sudo ./install_drivers

