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
#include "perf.h"
#include "playground_util/print_params.h"

#ifdef SHOW_CONV_PERF
#define PERF_START(n) perf_enable_counter(n)
#define PERF_END(n) perf_disable_counter(n)
#else
#define PERF_START(n)
#define PERF_END(n)
#endif

//
// This file contains specialized conv 2D implementations to support
// MobileNet v2 models
//
namespace tflite {
namespace reference_integer_ops {

inline static int CalculateChannelsPerBatch(int input_depth, int output_depth) {
  // Each pixel processed requires:
  // - output_depth words to be stored in output_params, and
  // - input_depth * output_depth words stored in filter values.
  // If either of these limits are exceeded, we break processing into batches

  int channels_per_batch = output_depth;

  // Limit by output params
  channels_per_batch = std::min(channels_per_batch, MAX_CONV_OUTPUT_PARAMS);

  // Limit by filter values
  channels_per_batch =
      std::min(channels_per_batch, MAX_FILTER_VALUES_PER_PIXEL / input_depth);

#ifdef USE_CONV_SMALL_BATCHES
  channels_per_batch = std::min(channels_per_batch, 2048);
#endif

  // Round to nearest lower multiple of 4
  channels_per_batch &= ~3;

  return channels_per_batch;
}

inline static void LoadOutputChannelWeights(const int32_t*& output_multiplier,
                                            const int32_t*& output_shift,
                                            const int32_t*& bias_data,
                                            int batch_size) {
  PERF_START(3);
  CFU_SET_OUTPUT_BATCH_SIZE(batch_size);
  for (int i = 0; i < batch_size; i += 4) {
    CFU_STORE_OUTPUT_MULTIPLIER(*(output_multiplier++));
    CFU_STORE_OUTPUT_MULTIPLIER(*(output_multiplier++));
    CFU_STORE_OUTPUT_MULTIPLIER(*(output_multiplier++));
    CFU_STORE_OUTPUT_MULTIPLIER(*(output_multiplier++));
  }
  for (int i = 0; i < batch_size; i += 4) {
    CFU_STORE_OUTPUT_SHIFT(*(output_shift++));
    CFU_STORE_OUTPUT_SHIFT(*(output_shift++));
    CFU_STORE_OUTPUT_SHIFT(*(output_shift++));
    CFU_STORE_OUTPUT_SHIFT(*(output_shift++));
  }
  for (int i = 0; i < batch_size; i += 4) {
    CFU_STORE_OUTPUT_BIAS(*(bias_data++));
    CFU_STORE_OUTPUT_BIAS(*(bias_data++));
    CFU_STORE_OUTPUT_BIAS(*(bias_data++));
    CFU_STORE_OUTPUT_BIAS(*(bias_data++));
  }
  PERF_END(3);
}

inline static void LoadFilterValues(const uint32_t*& filter_words,
                                    int num_words) {
  PERF_START(4);
  for (int i = 0; i < num_words; i += 8) {
    CFU_STORE_FILTER_VALUE(*(filter_words++));
    CFU_STORE_FILTER_VALUE(*(filter_words++));
    CFU_STORE_FILTER_VALUE(*(filter_words++));
    CFU_STORE_FILTER_VALUE(*(filter_words++));
    CFU_STORE_FILTER_VALUE(*(filter_words++));
    CFU_STORE_FILTER_VALUE(*(filter_words++));
    CFU_STORE_FILTER_VALUE(*(filter_words++));
    CFU_STORE_FILTER_VALUE(*(filter_words++));
  }
  PERF_END(4);
}

inline static void LoadInputValues(const uint32_t*& input_ptr,
                                   int input_depth_words) {
  PERF_START(6);
  for (; input_depth_words > 2; input_depth_words -= 4) {
    CFU_STORE_INPUT_VALUE(*(input_ptr++));
    CFU_STORE_INPUT_VALUE(*(input_ptr++));
    CFU_STORE_INPUT_VALUE(*(input_ptr++));
    CFU_STORE_INPUT_VALUE(*(input_ptr++));
  }
  if (input_depth_words == 2) {
    CFU_STORE_INPUT_VALUE(*(input_ptr++));
    CFU_STORE_INPUT_VALUE(*(input_ptr++));
  }
  PERF_END(6);
}

inline static void UnloadOutputValues(uint32_t*& output_ptr, int num_words) {
  PERF_START(7);
  for (; num_words > 2; num_words -= 4) {
    *(output_ptr++) = CFU_GET_OUTPUT();
    *(output_ptr++) = CFU_GET_OUTPUT();
    *(output_ptr++) = CFU_GET_OUTPUT();
    *(output_ptr++) = CFU_GET_OUTPUT();
  }
  if (num_words == 2) {
    *(output_ptr++) = CFU_GET_OUTPUT();
    *(output_ptr++) = CFU_GET_OUTPUT();
  }
  PERF_END(7);
}

// Fixed-point per-channel-quantization convolution reference kernel.
void Mnv2ConvPerChannel1x1(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const int32_t* bias_data, const RuntimeShape& output_shape,
    int8_t* output_data) {
  PERF_START(2);
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
  const uint32_t* filter_words = (const uint32_t*)filter_data;
  const int num_pixels = output_height * output_width;
  const int channels_per_batch =
      CalculateChannelsPerBatch(input_depth, output_depth);
  const int num_batches =
      (channels_per_batch - 1 + output_depth) / channels_per_batch;
  PERF_END(2);

  for (int batch = 0; batch < num_batches; batch++) {
    const int batch_base = batch * channels_per_batch;
    const int batch_end =
        std::min(output_depth, batch_base + channels_per_batch);
    const int batch_size = batch_end - batch_base;

    // Load up output channel parameters and filter values
    LoadOutputChannelWeights(output_multiplier, output_shift, bias_data,
                             batch_size);
    LoadFilterValues(filter_words, batch_size * input_depth_words);

    PERF_START(5);
    // Reset input and output pointers
    const uint32_t* input_ptr = (uint32_t*)input_data;
    uint32_t* output_ptr = (uint32_t*)(output_data + batch_base);

    // Load twice on first loop, no load on last loop and once every other
    // time.
    LoadInputValues(input_ptr, input_depth_words);
    for (int p = 0; p < num_pixels - 1; p++) {
      LoadInputValues(input_ptr, input_depth_words);
      CFU_MACC_RUN();
      UnloadOutputValues(output_ptr, batch_size / 4);
      output_ptr += (output_depth - batch_size) / 4;
    }
    CFU_MACC_RUN();
    UnloadOutputValues(output_ptr, batch_size / 4);
    PERF_END(5);
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
