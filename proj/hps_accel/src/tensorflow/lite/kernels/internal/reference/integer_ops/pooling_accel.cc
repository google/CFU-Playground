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
  // Reference implementation
  TFLITE_DCHECK_LE(params.quantized_activation_min,
                   params.quantized_activation_max);
  TFLITE_DCHECK_GE(params.quantized_activation_min,
                   std::numeric_limits<int8_t>::min());
  TFLITE_DCHECK_LE(params.quantized_activation_max,
                   std::numeric_limits<int8_t>::max());
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int depth = MatchingDim(input_shape, 3, output_shape, 3);
  const int input_height = input_shape.Dims(1);
  const int input_width = input_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  const int stride_height = params.stride_height;
  const int stride_width = params.stride_width;
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      for (int out_x = 0; out_x < output_width; ++out_x) {
        for (int channel = 0; channel < depth; ++channel) {
          const int in_x_origin =
              (out_x * stride_width) - params.padding_values.width;
          const int in_y_origin =
              (out_y * stride_height) - params.padding_values.height;
          // Compute the boundaries of the filter region clamped so as to
          // ensure that the filter window fits in the input array.
          const int filter_x_start = std::max(0, -in_x_origin);
          const int filter_x_end =
              std::min(params.filter_width, input_width - in_x_origin);
          const int filter_y_start = std::max(0, -in_y_origin);
          const int filter_y_end =
              std::min(params.filter_height, input_height - in_y_origin);
          int8_t max = std::numeric_limits<int8_t>::lowest();
          for (int filter_y = filter_y_start; filter_y < filter_y_end;
               ++filter_y) {
            for (int filter_x = filter_x_start; filter_x < filter_x_end;
                 ++filter_x) {
              const int in_x = in_x_origin + filter_x;
              const int in_y = in_y_origin + filter_y;
              max = std::max(
                  max,
                  input_data[Offset(input_shape, batch, in_y, in_x, channel)]);
            }
          }
          max = std::max<int8_t>(max, params.quantized_activation_min);
          max = std::min<int8_t>(max, params.quantized_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, channel)] =
              static_cast<int8_t>(max);
        }
      }
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
