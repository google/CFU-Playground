
# `basic_cfu` test program

`basic_cfu` is a simple bare-metal program that does not use or link in the TFLM library.  Thus its binary is small and it loads to the board quickly.

### Compiling

You should be able to run this command in this directory:

```
make
```

You should see this:

```
  CC       ./src/cfu.c  cfu.o
  CC       ./src/main.c main.o
  AS       ./src/crt0-vexriscv.S        crt0-vexriscv.o
  LD       basic.elf
  OBJDUMP  basic.elf
  OBJCOPY  basic.bin
  IHEX     basic.ihex
```

You can `make clean` to start over.


### Usage

If you need to load the SoC bitstream, go to the directory above and run `make prog`.

In this directory, run this:

```
make run
```

Error checking is minimal, especially with regard to finding the correct USB device.

Once running, the program will flash the LEDs for a couple of seconds, and then present a menu of interactive keyboard options.  To see the menu again, hit '?'.

Options 'c', 'd', and 's' attempt to access the CFU.   If the CFU is not handling the CFU-CPU handshaking correctly, the application will hang here.  At that point, you can press the 'PROG' button, or ctrl-C out of `litex_term` and rerun.

This is the full menu:

```
0: switch to perf counter 0 and show value
1: switch to perf counter 1 and show value
e: enable current perf counter
p: pause current perf counter
z: zero-out current perf counter, and also zero-out mcycle
m: show current value of mcycle (mcycle is not pausable)

c: run preset CFU test (run fixed values through funct0, funct1, and funct2)
d: interactive CFU test -- you supply the operands
s: run test of CFU against software emulation

?: show menu again
```



