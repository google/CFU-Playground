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
namespace {

inline bool PaddingsAre(const tflite::PadParams& op_params, int l0, int l1,
                        int l2, int l3, int r0, int r1, int r2, int r3) {
  if (op_params.left_padding[0] != l0) return false;
  if (op_params.left_padding[1] != l1) return false;
  if (op_params.left_padding[2] != l2) return false;
  if (op_params.left_padding[3] != l3) return false;
  if (op_params.right_padding[0] != r0) return false;
  if (op_params.right_padding[1] != r1) return false;
  if (op_params.right_padding[2] != r2) return false;
  if (op_params.right_padding[3] != r3) return false;
  return true;
}

// Copies n blocks
inline void CopyBlocks(const uint32_t*& input, uint32_t*& output, int n) {
  const uint32_t* end = input + 4 * n;
  while (input != end) {
    output[0] = input[0];
    output[1] = input[1];
    output[2] = input[2];
    output[3] = input[3];
    output += 4;
    input += 4;
  }
}

// Pads n blocks with pad_word
inline void PadBlocks(uint32_t*& output, int n, uint32_t pad_word) {
  uint32_t* end = output + 4 * n;
  while (output != end) {
    output[0] = pad_word;
    output[1] = pad_word;
    output[2] = pad_word;
    output[3] = pad_word;
    output += 4;
  }
}

// Pads assuming depths are a multiple of 16
void Pad16ByteBlocks(const tflite::PadParams& op_params,
                     const RuntimeShape& input_shape, const uint32_t* input,
                     uint32_t pad_word, const RuntimeShape& output_shape,
                     uint32_t* output) {
  // Depth in 4 word "blocks"
  int depth_blocks = input_shape.Dims(3) / 16;
  int above = op_params.left_padding[1];
  int left_blocks = depth_blocks * op_params.left_padding[2];
  int right_blocks = depth_blocks * op_params.right_padding[2];
  int below = op_params.right_padding[1];
  int input_rows = input_shape.Dims(1);
  int row_blocks = depth_blocks * input_shape.Dims(2);
  int whole_row_blocks = left_blocks + row_blocks + right_blocks;

  for (int i = 0; i < above; i++) {
    PadBlocks(output, whole_row_blocks, pad_word);
  }
  for (int i = 0; i < input_rows; i++) {
    PadBlocks(output, left_blocks, pad_word);
    CopyBlocks(input, output, row_blocks);
    PadBlocks(output, right_blocks, pad_word);
  }
  for (int i = 0; i < below; i++) {
    PadBlocks(output, whole_row_blocks, pad_word);
  }
}

}  // anonymous namespace

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
  int output_batches = output_shape.Dims(0);
  if (input_batches != 1 || output_batches != 1) return false;
  int input_height = input_shape.Dims(1);
  int input_width = input_shape.Dims(2);
  int input_depth = input_shape.Dims(3);
  int output_height = output_shape.Dims(1);
  int output_width = output_shape.Dims(2);
  int output_depth = output_shape.Dims(3);

  if (input_depth != output_depth) return false;

  // Check for input layer
  if (input_depth == 1) {
    if (input_height != 240 || input_width != 320) return false;
    if (output_height != 242 || output_width != 322) return false;
    return PaddingsAre(op_params, 0, 1, 1, 0, 0, 1, 1, 0);

    // Check for other layers
  } else if (input_depth > 1 && input_depth % 16 == 0) {
    return PaddingsAre(op_params, 0, 0, 0, 0, 0, 0, 0, 0) ||
           PaddingsAre(op_params, 0, 0, 1, 0, 0, 0, 2, 0) ||
           PaddingsAre(op_params, 0, 1, 1, 0, 0, 0, 2, 0) ||
           PaddingsAre(op_params, 0, 0, 1, 0, 0, 2, 2, 0) ||
           PaddingsAre(op_params, 0, 1, 1, 0, 0, 2, 2, 0);
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
  } else {
    uint8_t pv = static_cast<uint8_t>(pad_value);
    uint32_t pad_word = pv | pv << 8 | pv << 16 | pv << 24;
    Pad16ByteBlocks(op_params, input_shape,
                    reinterpret_cast<const uint32_t*>(input_data), pad_word,
                    output_shape, reinterpret_cast<uint32_t*>(output_data));
  }
}

}  // namespace reference_ops
}  // namespace tflite
