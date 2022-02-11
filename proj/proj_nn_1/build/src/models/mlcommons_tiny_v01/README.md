# Contents

This folder contains tests for the reference models found at
[github.com/mlcommons/tiny](https://github.com/mlcommons/tiny).

This folder does not implement the benchmark routines, rather it simply tests
the quantized reference models on preprocessed input.

## Models

### Anomaly Detection

This model is located at
`third_party/mlcommons/tiny/v0.1/training/anomaly_detection/trained_models/ad01_int8.tflite`.
The tests for this model are located in the `anomd/` folder in this directory.
Inputs to the tests have already been quantized, and are located in
`anomd/test_data`. The output of this model requires post processing, which is
not implemented in the tests -- rather a 32-bit xor reduction is used to check
for output equivalence to expected results.

> To include this model in your project, define the identifier
> `INLCUDE_MODEL_MLCOMMONS_TINY_V01_ANOMD`.

### Image Classification

This model is located at
`third_party/mlcommons/tiny/v0.1/training/image_classification/trained_models/pretrainedResnet_quant.tflite`.
The tests for this model are located in the `imgc/` folder in this directory.
Inputs to the tests have already been quantized, and are located in
`imgc/test_data`.

> To include this model in your project, define the identifier
> `INLCUDE_MODEL_MLCOMMONS_TINY_V01_IMGC`.

### Keyword Spotting

This model is located at
`third_party/mlcommons/tiny/v0.1/training/keyword_spotting/trained_models/kws_ref_model.tflite`.
The tests for this model are located in the `kws/` folder in this directory.
Inputs to the tests do not need to be quantized and are located in
`kws/test_data`.

> To include this model in your project, define the identifier
> `INLCUDE_MODEL_MLCOMMONS_TINY_V01_KWS`.

### Visual Wake Words

This model is located at
`third_party/mlcommons/tiny/v0.1/training/visual_wake_words/trained_models/vww_96_int8.tflite`.
The tests for this model are located in the `vww/` folder in this directory.
Inputs to the tests have already been quantized, and are located in
`vww/test_data`.

> To include this model in your project, define the identifier
> `INLCUDE_MODEL_MLCOMMONS_TINY_V01_VWW`.
