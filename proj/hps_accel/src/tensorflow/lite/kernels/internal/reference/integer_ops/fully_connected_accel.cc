/*
 * Copyright 2022 The CFU-Playground Authors
 * Copyright 2019 The TensorFlow Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "tensorflow/lite/kernels/internal/reference/integer_ops/fully_connected_accel.h"

#include <cstdio>

#include "tensorflow/lite/kernels/internal/common.h"

namespace tflite {
namespace reference_integer_ops {

// Determine whether operation is suitable for acceleration
bool CanAccelerateFullyConnected(const FullyConnectedParams& params,
                                 const RuntimeShape& filter_shape,
                                 const int32_t* bias_data,
                                 const RuntimeShape& output_shape) {
  if (params.input_offset != 128) return false;
  if (params.weights_offset != 0) return false;
  if (bias_data == NULL) return false;
  if (filter_shape.Dims(1) % 16 != 0) return false;
  if (output_shape.Dims(0) != 1) return false;
  return true;
}

// Accelerated implementation
void AccelerateFullyConnected(
    const FullyConnectedParams& params, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const int32_t* bias_data, const RuntimeShape& output_shape,
    int8_t* output_data) {
  const int32_t input_offset = 128;
  const int32_t output_offset = params.output_offset;
  const int32_t output_multiplier = params.output_multiplier;
  const int output_shift = params.output_shift;
  const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = params.quantized_activation_max;
  TFLITE_DCHECK_GE(filter_shape.DimensionsCount(), 2);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 2);

  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  const int filter_dim_count = filter_shape.DimensionsCount();
  const int output_depth = output_shape.Dims(1);
  TFLITE_DCHECK_LE(output_depth, filter_shape.Dims(filter_dim_count - 2));
  const int accum_depth = filter_shape.Dims(filter_dim_count - 1);
  for (int out_c = 0; out_c < output_depth; ++out_c) {
    const int8_t* ip = input_data;
    int32_t acc = 0;
    for (int d = 0; d < accum_depth; d += 4) {
      acc += *filter_data++ * (input_offset + *ip++);
      acc += *filter_data++ * (input_offset + *ip++);
      acc += *filter_data++ * (input_offset + *ip++);
      acc += *filter_data++ * (input_offset + *ip++);
    }
    acc += bias_data[out_c];
    acc = MultiplyByQuantizedMultiplier(acc, output_multiplier, output_shift);
    acc += output_offset;
    acc = std::max(acc, output_activation_min);
    acc = std::min(acc, output_activation_max);
    output_data[out_c] = static_cast<int8_t>(acc);
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
