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

#include "tensorflow/lite/kernels/internal/reference/integer_ops/pooling_accel.h"

#include <algorithm>
#include <cstdio>

#include "tensorflow/lite/kernels/internal/common.h"

namespace tflite {
namespace reference_integer_ops {

// Determine whether operation is suitable for acceleration
bool CanAccelerateMaxPool(const PoolParams& params,
                          const RuntimeShape& input_shape,
                          const RuntimeShape& output_shape) {
  if (params.padding_values.height != 0) return false;
  if (params.padding_values.width != 0) return false;
  if (params.quantized_activation_min != -128) return false;
  if (params.quantized_activation_max != 127) return false;
  if (params.stride_height != 2 || params.stride_width != 2) return false;
  if (params.filter_height != 2 || params.filter_width != 2) return false;

  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int depth = MatchingDim(input_shape, 3, output_shape, 3);
  if (batches != 1) return false;
  if (depth == 0 || depth % 16 != 0) return false;

  return true;
}

// Accelerate the operation
void AccelerateMaxPool(const PoolParams& params,
                       const RuntimeShape& input_shape,
                       const int8_t* input_data,
                       const RuntimeShape& output_shape, int8_t* output_data) {
  const int depth = MatchingDim(input_shape, 3, output_shape, 3);
  const int input_width = input_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  const int stride_height = 2;
  const int stride_width = 2;
  const int input_row_size = input_width * depth;
  for (int out_y = 0; out_y < output_height; ++out_y) {
    for (int out_x = 0; out_x < output_width; ++out_x) {
      for (int channel = 0; channel < depth; ++channel) {
        const int in_x_origin = out_x * stride_width;
        const int in_y_origin = out_y * stride_height;
        int input_offset =
            Offset(input_shape, 0, in_y_origin, in_x_origin, channel);
        int8_t max = input_data[input_offset];
        max = std::max(max, input_data[input_offset + depth]);
        input_offset += input_row_size;
        max = std::max(max, input_data[input_offset]);
        max = std::max(max, input_data[input_offset + depth]);
        output_data[Offset(output_shape, 0, out_y, out_x, channel)] =
            static_cast<int8_t>(max);
      }
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
