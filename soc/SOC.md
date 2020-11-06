
## General notes

I've turned off the UART bridge since I've been using the Etherbone bridge.
To re-enable, uncomment the relavant lines in soc.py.


## Inital clone

After you clone this repo, cd into it and get the submodules:
```
git submodule update --recursive --init
```


## Building non-CFU version

`cd` into the soc/ subdirectory.

You must have python3.7 or higher:

```
python3 ./soc.py --build --csr-csv csr.csv [--with-etherbone] [--load]
```
The output bitstream will be in ./build

To change between the debug and non-debug versions of the CPU, you must edit soc.py.


## Adding CFUs

There's a new option to `soc.py`: `--cfu <path_to_cfu.v>`.  When you specify this,
it also chooses the CFU-enabled version of VexRiscv.   (Note that the `deps/pythondata_cpu_vexriscv` 
submodule points to the `dev` branch on **my** fork).   We then use a wrapper that contains the CPU and CFU, 
and presents a standard (non-CFU) port interface to the surrounding SoC.

I've provided a very simple CFU at `./cfu/Cfu.v`.    To build an SoC with it, I use:

```
time python3 ./soc.py --build --csr-csv csr.csv --cfu ./cfu/Cfu.v [--with-etherbone] [--load]
```

Currently the setup is such that you must specify one module as the CFU.  However, 3 bits of
function code are provided to the CFU, so you can implement up to eight different functions within that module.

Other CFUs to try:

* `pipe/Cfu.v`: two-stage pipeline.   Stalls (and refuses new input) when it gets backpressure sending results back to the CPU.  Single-function (ignore the function code input).
* `fib/Cfu.v`: Fibonacci, iterative, variable latency; refuses new input while it is working on a calculation.  Single-function (ignore the function code input).

Later, In your own CFU projects, you will build the SoC using a different script, and with your own Cfu.v.   
But it will depend on the other Verilog files generated here, in build/arty/gateware/.


## Software to exercise the CFU

```
cd basic_cfu
make
lxterm --speed 115200 --kernel basic.bin /dev/ttyUSB*
```

The LEDs will flash for a bit, then you should see a hello world message.   
Type keys to get an echo.  Odd keys ('a', 'c', 'e', etc.) give a double echo (intentionally).

Hit 'c' to run the CFU test with fixed input values.

Hit 'd' to run the CFU test where you the user can type in the two input operand values.   

Hit 'z' to zero-out performance counters (including `mcycle`)

Hit 'm' to display `mcycle` counter (not pausable).

Hit '0' to display and switch to pausable performance counter #0.

Hit '1' to display and switch to pausable performance counter #1.

Hit 'e' to enable the current counter.

Hit 'p' to pause the current counter.


These work with whichever CFU you built the SoC with, although the column titles (bytesum, byteswap, and bitrev) only apply to `./cfu/Cfu.v`.


