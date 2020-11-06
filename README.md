# CFU Playground

### Setup

Clone this repo, `cd` into it, then get the first level of submodules (don't do `--recursive`):
```
git submodule init
git submodule update
```
### Use

Build the SoC, optionally with Etherbone, and load it onto Arty:
```
pushd soc
python3.7 ./soc.py --build --csr-csv csr.csv --cfu cfu/Cfu.v [--with-etherbone] --load
popd
```

Build the program and execute it:
```
cd basic_cfu
make
lxterm --speed 115200 --kernel basic_cfu.bin /dev/ttyUSB*
```
(maybe you don't have `lxterm` in your path, but 

### Licensed under Apache-2.0 license

See the file `LICENSE`.
