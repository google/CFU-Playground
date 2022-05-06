# FCCM Tutorial Example

This example accelerator was created for the FCCM 2022 tutorial 
"CFU-Playground: Build Your Own Custom TinyML Processor".

https://www.fccm.org/workshop-tutorial-2022/

## Amaranth CFU

`cfu.py` contains a complete CFU written in Amaranth. It can perform
these functions:

* Operation 0: Reset accumulator
* Operation 1: 4-way multiply accumulate.
* Operation 2: Read accumulator

Test cases can be run by executing `cfu.py`:

```
$ ../../scripts/pyrun cfu.py
```

## Building and Running

To build and program a Digilent Arty board, first follow the standard [setup
instructions](https://cfu-playground.readthedocs.io/en/latest/setup-guide.html)
to install Symbiflow and a RISCV compiler. Then:

```
$ make TARGET=digilent_arty USE_SYMBIFLOW=1 prog
```

You should see the familiar flashing lights, then:

```
$ make TARGET=digilent_arty USE_SYMBIFLOW=1 BUILD_JOBS=8 prog
```

This will load the software and start a terminal. Interesting options are:

* 1 (Models), 1 (person detection int 8), 1 (person)   [[check this]]
* 3 (Project menu), 1 (Exercise CFU)

To ignore the CFU when running models, comment out this line:

```
# DEFINES += ACCEL_CONV2D
```

With gateware ignored, the inference times are very close to the inference
times as measured with `proj/proj_template`.

To use the CFU operation emulator defined in the `src/software_cfu.cc` file,
uncomment this line:

```
# DEFINES += CFU_SOFTWARE_DEFINED
```

While it is much slower, it is often convenient to use emulated operations
while debugging.


## `proj_menu.cc`

Contains snippets demonstrating the integration of the CFU with the SoC.

[[Insert instructions here]]

## Tensorflow Lite for Microcontrollers



