/* Copyright 2019 The TensorFlow Authors. All Rights Reserved.

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

#include <cstdio>

#include "fccm_cfu.h"
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/reference/integer_ops/conv.h"

namespace tflite {
namespace reference_integer_ops {

inline const uint32_t* as_word_ptr(const int8_t* byte_ptr) {
  return reinterpret_cast<const uint32_t*>(byte_ptr);
}

// Fixed-point per-channel-quantization convolution reference kernel.
void OneByOneConvPerChannel(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const int32_t* bias_data, const RuntimeShape& output_shape,
    int8_t* output_data) {
  // Get parameters.
  const int32_t output_offset = params.output_offset;

  // Set min and max value of the output.
  const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = params.quantized_activation_max;

  // Consistency check.
  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      for (int out_x = 0; out_x < output_width; ++out_x) {
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          const int in_y = out_y;
          const int in_x = out_x;
          const uint32_t* input_ptr = as_word_ptr(
              input_data + Offset(input_shape, batch, in_y, in_x, 0));
          const uint32_t* filter_ptr = as_word_ptr(
              filter_data + Offset(filter_shape, out_channel, 0, 0, 0));

          // We do 16 of these to Multiply-Accumulate 64 values
          cfu_reset();
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);

          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);

          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);

          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);
          cfu_accumulate(*input_ptr++, *filter_ptr++);

          int32_t acc = cfu_read();
          if (bias_data) {
            acc += bias_data[out_channel];
          }
          acc = MultiplyByQuantizedMultiplier(
              acc, output_multiplier[out_channel], output_shift[out_channel]);
          acc += output_offset;
          acc = std::max(acc, output_activation_min);
          acc = std::min(acc, output_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, out_channel)] =
              static_cast<int8_t>(acc);
        }
      }
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
