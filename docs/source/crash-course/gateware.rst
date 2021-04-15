==========================================================
Building FPGA Gateware with Verilog and nMigen: A Tutorial
==========================================================

This page takes the reader through a hands-on tutorial on FPGA, Verilog and
nMigen.

Field Programmable Gate Arrays are fascinating devices that can efficiently
perform all kinds of computing tasks. A configuration for and FPGA is known as
'gateware'.

There are a variety of ways to configure FPGAs. Verilog is perhaps the most
well known and best supported. Learning Verilog is good way to begin to
understand how FPGAs work.

It is possible to write CFUs in Verilog, but for more sophisticated CFUs we use
nMigen to generate Verilog.

------------
Getting Help
------------

Try not to get stuck for long periods of time. Generally, you'll learn more
quickly by getting help from someone who has done it before rather than
struggling yourself for long periods of time. See: :doc:`getting-help`.


----------------
Before You Begin
----------------

Obtain Equipment
================

Obtain the following:

1. An Arty A7-35T (as per the :doc:`../setup-guide`).

2. A PMOD AMP2. PMOD is a connector standard for FPGA dev boards. PMOD AMP2 is
   a simple audio output board. (Digikey_ , `Element 14`_)

.. _Digikey: https://www.digikey.com.au/products/en/development-boards-kits-programmers/evaluation-boards-expansion-boards-daughter-cards/797?k=PMODAMP2&pkeyword=&sv=0&sf=0&FV=-8%7C797&quantity=&ColumnSort=0&page=1&pageSize=25
.. _`Element 14`: https://au.element14.com/digilent/410-233/modlue-pmod-audio-amp-2-5w-class/dp/2311269?ost=pmod+amp2

3. Speaker with 3.5mm plug. Obtain this from eBay or any electronics store. 

4. Optional: UPduino. A small FGPA dev board which will make the nMigen
   tutorial a little easier and faster. (Order from tindie.) 
   * The UPduino often goes out of stock and sometimes delivery times are long.
   * It's more than possible to run the tutorial from an Arty A7.  

.. _`Order from Tindie`: https://www.tindie.com/products/tinyvision_ai/upduino-v30-low-cost-lattice-ice40-fpga-board/

5. Micro-USB cable. You probably already have one.

Set Up
======

Follow the instructions at :doc:`../setup-guide` to set up Vivado and the CFU Playground.

----------------------------------------------
Part 1: Verilog Programming With Xilinx Vivado
----------------------------------------------

Verilog
    ... is a hardware description language (HDL) used to model electronic
    systems. It is most commonly used in the design and verification of digital
    circuits at the register-transfer level of abstraction. 

    -- Wikipedia: `Verilog <https://en.wikipedia.org/wiki/Verilog>`_

Vivado Design Suite
    is a software suite produced by Xilinx for synthesis and analysis of HDL
    designs Vivado Design Suite took 1000 person-years and cost US$200
    million.

    -- Wikipedia: `Xilinx Vivado <https://en.wikipedia.org/wiki/Xilinx_Vivado>`_

Getting Familiar with The Arty A7
=================================

Work though tcal-x's Arty tutorials at `github.com/tcal-x/misc
<https://github.com/tcal-x/misc>`. To do tutorial 2 you will either need to git
clone the repo or download the top.bit file

Board Definition file 
=====================

The board definition file tells Vivado about the eval board you're using -
which LEDs and switches are connected and to which pins of the FPGA.

1. Download master.zip_ to your Downloads directory.

.. _master.zip: https://github.com/Digilent/vivado-boards/archive/master.zip?_ga=2.236032133.563501946.1602061710-858136677.1600823904

2. Now, unzip the file and copy do your Xilinx directory

.. code-block:: bash

   $ cd ~/Downloads
   $ unzip master.zip
   $ cd ~/Downloads/vivado-boards-master/new
   $ cp -r board_files/ ~/tools/Xilinx/Vivado/2020.1/data/boards/

Your First Verilog Program
==========================

Start Vivado from the Linux Application menu, then follow along with this
YouTube video from Graham Chow: `Verilog using Vivado on Digilent Arty Xilinx
FPGA.`__

.. __: https://www.youtube.com/watch?v=RAUm9mR4-W4

This video is for a slightly older version of Arty and Vivado, so watch out for
changed menu item names and so forth.

* For board, choose Arty A7-35T
* Make a subdirectory for all your vivado projects. I chose ~/vivado, and this
  project's files were stored in ~/vivado/project_1
* XDC files:

  * XDC files are linked from the `Arty A7 Reference`_ page
  * Download Arty-A7-35-Master.xdc_ into your project's folder.
  * From the "Add Sources" dialog, make sure you choose "Add or create constraints"

* Graham says "top's always pretty popular". Verilog designs are hierarchical,
  so the name "top" is often used for the top of the hierarchy.
* At the programming step, you'll find the generated bitstream in the "runs"
  directory. For example, on my machine, the file is at:
  ``/home/avg/vivado/project_1/project_1.runs/impl_1/top.bit``

.. _`Arty A7 Reference`: https://reference.digilentinc.com/reference/programmable-logic/arty-a7/start
.. _Arty-A7-35-Master.xdc: https://raw.githubusercontent.com/Digilent/digilent-xdc/master/Arty-A7-35-Master.xdc

Here is the code Graham uses:

.. code-block:: verilog

    module top(
        input CLK100MHZ,
        output reg [3:0] led,
        input [3:0] sw
        );

        always @ (posedge CLK100MHZ)
        begin
            if (sw[0] == 0)
            begin
                led <= 4'b0000;
            end
            else
            begin
                led <= 4'b1111;
            end
        end
    endmodule

This downloadable guide from Xilinx contains more information about using
Vivado: `UG892 - Vivado Design Suite User Guide: Design Flows Overview`__.

.. __: https://www.xilinx.com/support/documentation/sw_manuals/xilinx2020_1/ug892-vivado-design-flows-overview.pdf


FPGA4Fun - Introductory material
================================

fpga4fun.com is full of well researched material relevant to FPGA beginners,
presented in a - well, fun - manner. It is (by far) the best online
introduction to FPGAs we have found.

Start off by reading through the material under FPGA introduction in the left
hand menu (scroll way down). The most relevant pages are:

* `What are FPGAs? <https://www.fpga4fun.com/FPGAinfo1.html>`
* `How FPGAs work <https://www.fpga4fun.com/FPGAinfo2.html>`
* `Internal RAM <https://www.fpga4fun.com/FPGAinfo3.html>`
* `FPGA pins <https://www.fpga4fun.com/FPGAinfo4.html>`
* `Clocks and global lines <https://www.fpga4fun.com/FPGAinfo5.html>`



FPGA4Fun - Music Box
====================

The `Music box tutorials`__ will teach you the basics of Verilog and how FPGAs
do computation. Instead of putting things together on a breadboard, we'll use a
PMOD AMP2 and a plug-in speaker.

.. __: https://www.fpga4fun.com/MusicBox.html

1. With your Arty board unpowered, plug the PMOD AMP2 into the top row of header JD, and plug a speaker into the PMOD.

.. image:: ../images/arty_with_amp.jpg
   :height: 300px
   :alt: View of an Arty A7 plugged into a PMOD2 and a speaker

2. Read through the first section of `Music box 1 - Simple beep`__.

.. __: https://www.fpga4fun.com/MusicBox1.html

3. Now start a new project in pretty much the same you did before while following along to the Youtube video:

   a. Start a new project in your $HOME/vivado directory
   b. Copy in the .xdc file
   c. In the XDC file, uncomment

      * CLK100MHz lines Clock lines
      * The switches - sw[0] to sw[3]
      * The leds - led[0] to led[3]
      * Under PMOD header JD, uncomment jd[0] to jd[3] 

4. Use this Verilog:

.. code-block:: verilog

  module top(
      // ***(A)***
      input CLK100MHZ,
      output [3:0] jd,
      output [3:0] led,
      input [3:0] sw
      );

  // ***(B)***
  // first create an 18bit binary counter  
  reg [17:0] counter;
  always @(posedge CLK100MHZ) counter <= counter+1;

  // and use the most significant bit (MSB) of the counter to drive the speaker
  wire speaker_out = counter[17];

  // ***(C)***
  // EITHER 
  // (1) you wish to annoy your neighbors, so send through the full speaker volume,  
  //assign jd[0] = speaker_out
  // OR 
  // (2) just send through the 1/64th of the signal by only sending signal when last 6 bits of counter are zero 
  assign jd[0] = speaker_out & (counter[5:0] == 0);

  // ***(D)***
  // Set switch 3 to toggle shutdown pin, turning amplifier on and off.
  // If you have housemates/family at home, you almost certainly need this
  assign jd[3] = sw[3];

  // ***(E)***
  // LEDs to help with debugging
  assign led[0] = speaker_out;   // Current wave form
  assign led[1] = jd[0];         // Attenuated signal sent to PMOD AMP
  assign led[3] = sw[3];
      
  endmodule


5. Note the differences between the above and the (much shorter) Verilog code on the FPGA4Fun site.

   a. Note that this Verilog puts the variable types inside the module
      statement, but fpga4fun has them outside. Both work, but the way shown here
      is more modern.
   b. We use an 18bit counter instead of a 16bit counter because we have a
      100MHz clock rather than 25 MHz clock. If that doesn't make sense, please
      ask.
   c. If we just toggle the PMOD output pin so that it's 50% on and 50% off ,
      the result is really quite loud. Instead, we "&" the speaker_out wire with
      an expression so that speaker_out == 1 causes the speaker to be on only
      1/64th of the time.
   d. jd[0] corresponds to pin 1 on pmod connector JD.
   e. jd[3] needs to be set high to enable output - check the PMODAMP2
      schematic, the SSM2377 datasheet and the PMODAMP2 packaging (below).
      We wire jd[3] to switch 3.
   f. To help with debugging, we plumb through some signals to the LEDs.

.. image:: ../images/pmodamp2_label.jpg
   :height: 200px
   :alt: Label of the PMOD AMP2 package, showing pin out

6. Synthesize and implement the design, then program it.
7. Toggle switch 3 to turn the sound on and off.

Make sure you understand what is going on here, then proceed through the rest of the sound box tutorials. 

Things to do:

* Understand each example before moving onto the next.
* Poke around in the GUI. Definitely "Open Implemented Design" at least once
  and try to figure out what you're looking at.
* See if you can figure out how to run Synthesis, Implementation and Bitstream
  generation with a single click. If you can't, ask! Having to click three
  things that each take ~1minute to complete is painful.
* Have fun.
* Ask questions.


More on FPGAs 
=============

Now that you've mastered the Music Box tutorials. A few important points to recap.

LUTs and FFs
  The basic elements of an FPGA are Lookup Tables (LUTs), Flip Flops (FFs) and routing to move signals between LUTs and FFs.

LUTs are not clocked.
Any signal applied to their input affects their output in a fairly short amount
of time - measured in nanoseconds. They hold no state. Their outputs are only
dependent on their inputs. LUTs can be chained together to produce complicated
functions. However if there are many LUTs or there is a long route between LUTs
in the chain, then calculating the result can take a long time.

FFs are clocked
  ... meaning they can only change their values on clock
  transitions. In Verilog, the clock transitions are specified like this:

.. code-block:: verilog

  always @(posedge clock) <statement>

This code means that the assignments in <statement> take place on every positive
edge of  the <clock> signal. After the positive edge, then the value of the
FF has changed and can affect other FFs on the next positive edge.

Everything happens all the time, unless you say not to.
  The way to enable logic sometimes and not others is to use an if statement:

.. code-block:: verilog

   always @(posedge clk) 
       if(counter==0) counter <= clkdivider-1;

Verilog's syntax is C-like, but it's not C.
  Expressions work mostly like C. However, the way state is treated is very
  different from a regular procedural language. There's no need for loops, for
  instance.

Counters are an important building block.
  They are used to manage state. It is common to derive control signals from
  counters. A common pattern to do something periodically is:

.. code-block:: verilog

   always @(posedge CLK100MHZ)
   begin
     if(counter==0) 
       counter <= reset_value; 
       << do something >>
     else 
       counter <= counter-1;
   end
