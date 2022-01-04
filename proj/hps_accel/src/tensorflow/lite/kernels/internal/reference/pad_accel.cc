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

#include "tensorflow/lite/kernels/internal/reference/pad_accel.h"

#include <cstdio>
#include <cstring>

namespace tflite {
namespace reference_ops {

// Determine whether operation is suitable for acceleration
bool CanAcceleratePad(const tflite::PadParams& op_params,
                      const RuntimeShape& input_shape, const int8_t* input_data,
                      const int8_t* pad_value_ptr,
                      const RuntimeShape& output_shape) {
  // Exclude common test conditions
  if (op_params.resizing_category != tflite::ResizingCategory::kImageStyle)
    return false;

  if (op_params.left_padding_count != 4 || op_params.right_padding_count != 4)
    return false;

  if (input_shape.DimensionsCount() != 4 || output_shape.DimensionsCount() != 4)
    return false;

  int input_batches = input_shape.Dims(0);
  int input_height = input_shape.Dims(1);
  int input_width = input_shape.Dims(2);
  int input_depth = input_shape.Dims(3);
  int output_batches = output_shape.Dims(0);
  int output_height = output_shape.Dims(1);
  int output_width = output_shape.Dims(2);
  int output_depth = output_shape.Dims(3);

  // Check for input layer
  if (input_batches == 1 && input_height == 240 && input_width == 320 &&
      input_depth == 1 && output_batches == 1 && output_height == 242 &&
      output_width == 322 && output_depth == 1) {
    if (op_params.left_padding[0] != 0) return false;
    if (op_params.left_padding[1] != 1) return false;
    if (op_params.left_padding[2] != 1) return false;
    if (op_params.left_padding[3] != 0) return false;
    if (op_params.right_padding[0] != 0) return false;
    if (op_params.right_padding[1] != 1) return false;
    if (op_params.right_padding[2] != 1) return false;
    if (op_params.right_padding[3] != 0) return false;
    return true;
  }

  // Didn't match any configuration
  return false;
}

// Accelerate the operation
void AcceleratePad(const tflite::PadParams& op_params,
                   const RuntimeShape& input_shape, const int8_t* input_data,
                   const int8_t* pad_value_ptr,
                   const RuntimeShape& output_shape, int8_t* output_data) {
  int8_t pad_value = *pad_value_ptr;
  int input_depth = input_shape.Dims(3);
  if (input_depth == 1) {
    // First, blank row
    memset(output_data, pad_value, 322);
    output_data += 322;
    // 240 rows of data with padding on each side
    for (int i = 0; i < 240; i++) {
      *output_data++ = pad_value;
      memcpy(output_data, input_data, 320);
      output_data += 320;
      input_data += 320;
      *output_data++ = pad_value;
    }
    // Last, blank row
    memset(output_data, pad_value, 322);
  }
}

}  // namespace reference_ops
}  // namespace tflite
