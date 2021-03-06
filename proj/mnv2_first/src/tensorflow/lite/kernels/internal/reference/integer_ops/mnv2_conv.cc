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

#include "mnv2_conv.h"

#include "tf_util/print_params.h"

//
// This file contains specialized conv 2D implementations to support
// MobileNet v2 models
//
namespace tflite {
namespace reference_integer_ops {

static inline int32_t macc(const int8_t* input_data, const int8_t* filter_data,
                           int out_channel, int in_channel, int input_depth,
                           int32_t input_offset) {
  int32_t input_val = input_data[in_channel];
  int32_t filter_val = filter_data[out_channel * input_depth + in_channel];
  return filter_val * (input_val + input_offset);
}

static inline int32_t accumulate(const int8_t* input_data,
                                 const int8_t* filter_data, int out_channel,
                                 int input_depth, int32_t input_offset) {
  int32_t acc = 0;
  for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
    acc += macc(input_data, filter_data, out_channel, in_channel, input_depth,
                input_offset);
  }
  return acc;
}

static inline int32_t post_process(int32_t acc, const int32_t* output_multiplier,
                                   const int32_t* output_shift,
                                   const int32_t* bias_data, int out_channel,
                                   int32_t output_offset,
                                   int32_t output_activation_min,
                                   int32_t output_activation_max) {
  acc += bias_data[out_channel];
  acc = MultiplyByQuantizedMultiplier(acc, output_multiplier[out_channel],
                                      output_shift[out_channel]);
  acc += output_offset;
  acc = std::max(acc, output_activation_min);
  acc = std::min(acc, output_activation_max);
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
  int num_pixels = output_height * output_width;
  for (int p = 0; p < num_pixels; p++) {
    for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
      int32_t acc = accumulate(input_data, filter_data, out_channel,
                               input_depth, input_offset);

      int32_t out = post_process(
          acc, output_multiplier, output_shift, bias_data, out_channel,
          output_offset, output_activation_min, output_activation_max);
      *(output_data++) = static_cast<int8_t>(out);
    }
    input_data += input_depth;
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
