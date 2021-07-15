# Tail ROM

This directory contains experimental code. It explores how parts of the
Tensorflow arena tail can be precalculated and placed into ROM.

## Capture tail data to place in ROM
To capture a ROM, use make_cache.sh

1. Use `make prog`, as normal to build and program a bitstream.

2. Edit `make_cache.sh` with the name of the model, and the menu item choices
   needed to load it.

    MENU_ITEMS="1 1"
    MODEL=pdti8

3. Run make_cache.sh:

    ./make_cache.sh

This will create two new source files: pdti8_cache.cc and pdti8_cache.h. These
generated files should be committed to the repository so they do not have to be
regenerated.

## Use Captured data

To use captured data from ROM:

1. Run `make load` as usual

2. From the menu choose "3: Project menu", then "1: Set cache for pdti8"

3. Exit to the main menu, then choose "1: TfLM Models menu" and then "1: Person
   Detection int8 model".

4. The model will then be loaded. You should see a message "Cached data matches
   model. Will use cached data."

5. Choose any option to run a model.


## How it works

`calc_once_data.cc` contains two types: a Capturer and a Cache. The Capturer
records certain memory allocation calls, and the content of the data that is
placed in the allocated memory. The data are printed to the console using
printf().

`extract_captured_data.py` script extracts the data from a console log and
builds a C++ source file and corresponding header file. The source file marks
data as `const`, which signals to the linker that the data may be stored in
ROM, for those platforms with ROM. The API to this data is a Cache object. A
`GetCacheXxxx()` function is provided in the generated code to retrieve the
object.

To use the captured data, the `Cache.InitForModel(model_data, model_length)`
is called before loading the TfLite model. See `proj_tflite.cc` for an example.
Then, when allocating memory, the cache is checked for a matching entry. If a
matching entry is found, then it is used.

This scheme requires modifying the TfLM code that allocates tail buffers and
fills them with data. See the code in the `src/tensorflow` directory for an
example of the changes required.