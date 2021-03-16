/* Copyright 2019 The TensorFlow Authors. All Rights Reserved.
   Copyright 2021 The CFU PLayground Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#include "tensorflow/lite/kernels/internal/reference/integer_ops/mnv2_conv.h"

#include "mnv2_cfu.h"
#include "tf_util/print_params.h"

//
// This file contains specialized conv 2D implementations to support
// MobileNet v2 models
//
namespace tflite {
namespace reference_integer_ops {

static inline int32_t accumulate(int input_depth, int32_t input_offset) {
  int32_t acc = 0;
  for (int in_channel = 0; in_channel < input_depth; in_channel += 8) {
    acc += CFU_MACC4_IMPLICIT(input_vals, filter_vals);
    acc += CFU_MACC4_IMPLICIT(input_vals, filter_vals);
  }
  return acc;
}

// Fixed-point per-channel-quantization convolution reference kernel.
void Mnv2ConvPerChannel1x1(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const int32_t* bias_data, const RuntimeShape& output_shape,
    int8_t* output_data) {
  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  const int32_t output_offset = params.output_offset;

  // Set min and max value of the output.
  const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = params.quantized_activation_max;

  // Consistency check
  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int input_depth = MatchingDim(input_shape, 3, filter_shape, 3);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }
  // Check dimensions of the tensors.
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);

  // Set parameters for op
  const int input_depth_words = input_depth / 4;
  CFU_SET_INPUT_DEPTH_WORDS(input_depth_words);
  CFU_SET_OUTPUT_DEPTH(output_depth);
  CFU_SET_INPUT_OFFSET(input_offset);
  CFU_SET_OUTPUT_OFFSET(output_offset);
  CFU_SET_ACTIVATION_MIN(output_activation_min);
  CFU_SET_ACTIVATION_MAX(output_activation_max);

  // Access filter data as words
  uint32_t* filter_words = (uint32_t*)filter_data;

// Do the processing in batches, by output channel. batch size is number of
// output channels processed per batch and it is chosen to avoid overflowing
// filter_data memory, and then rounded down to a multiple of 4.
//
// For each batch, the entire input will be read once
#ifdef USE_CONV_SMALL_BATCHES
  const int channels_per_batch =
      std::min(output_depth, (2048 / input_depth) / 4 * 4);
#else
  const int channels_per_batch =
      std::min(output_depth, (NUM_FILTER_DATA_BYTES / input_depth) / 4 * 4);
#endif

  const int num_pixels = output_height * output_width;
  const int num_batches =
      (channels_per_batch - 1 + output_depth) / channels_per_batch;

  for (int batch = 0; batch < num_batches; batch++) {
    const int batch_base = batch * channels_per_batch;
    const int batch_end =
        std::min(output_depth, batch_base + channels_per_batch);
    const int batch_size = batch_end - batch_base;

    // Load up parameters
    CFU_SET_OUTPUT_BATCH_SIZE(batch_size);
    for (int i = 0; i < batch_size; i++) {
      CFU_STORE_OUTPUT_MULTIPLIER(*(output_multiplier++));
    }
    for (int i = 0; i < batch_size; i++) {
      CFU_STORE_OUTPUT_SHIFT(*(output_shift++));
    }
    for (int i = 0; i < batch_size; i++) {
      CFU_STORE_OUTPUT_BIAS(*(bias_data++));
    }

    // Load up weights
    int num_filter_words = batch_size * input_depth / 4;
    for (int i = 0; i < num_filter_words; i++) {
      CFU_STORE_FILTER_VALUE(*(filter_words++));
    }
    // Reset input and output pointers
    const uint32_t* input_ptr = (uint32_t*)input_data;
    int8_t* output_ptr = output_data + batch_base;
    for (int p = 0; p < num_pixels; p++) {
      // Load one pixel's worth of input data
      for (int i = 0; i < input_depth_words; i++) {
        uint32_t val = *(input_ptr++);
        CFU_STORE_INPUT_VALUE(val);
      }

      for (int out_channel = batch_base; out_channel < batch_end;
           ++out_channel) {
        int32_t acc = accumulate(input_depth, input_offset);

        int32_t out = CFU_POST_PROCESS(acc);
        *(output_ptr++) = static_cast<int8_t>(out);
      }
      CFU_MARK_INPUT_READ_FINISHED();

      output_ptr += output_depth - batch_size;
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
