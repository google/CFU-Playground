/*
 * Copyright 2021 The CFU-Playground Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "conv2d_call.h"

#include <cstdio>

#include "playground_util/dump.h"
#include "tensorflow/lite/kernels/internal/reference/integer_ops/conv.h"
#include "tflite.h"

void test_conv2d(const Conv2DData* data) {
  printf("Testing Conv2D %s\n", data->name);
  // Copy input arena
  int8_t* arena_input = reinterpret_cast<int8_t*>(tflite_tensor_arena);
  auto input_shape =
      *(reinterpret_cast<const tflite::RuntimeShape*>(data->input_shape));
  for (int i = 0; i < input_shape.FlatSize(); i++) {
    arena_input[i] = data->input_data[i];
  }
  int8_t* arena_output =
      reinterpret_cast<int8_t*>(tflite_tensor_arena) + 128 * 1024;

  const tflite::RuntimeShape& output_shape =
      *(reinterpret_cast<const tflite::RuntimeShape*>(data->output_shape));
  tflite::reference_integer_ops::ConvPerChannel(
      *(reinterpret_cast<const tflite::ConvParams*>(data->params)),
      reinterpret_cast<const int32_t*>(data->output_multiplier),
      reinterpret_cast<const int32_t*>(data->output_shift), input_shape,
      reinterpret_cast<const int8_t*>(arena_input),
      *(reinterpret_cast<const tflite::RuntimeShape*>(data->filter_shape)),
      reinterpret_cast<const int8_t*>(data->filter_data),
      *(reinterpret_cast<const tflite::RuntimeShape*>(data->bias_shape)),
      reinterpret_cast<const int32_t*>(data->bias_data), output_shape,
      arena_output);

  // Check for differences with output
  int diff_count = 0;
  int first_diff = 0;
  int num_words = output_shape.FlatSize() / 4;
  const int32_t* arena_words = reinterpret_cast<const int32_t*>(arena_output);
  const int32_t* expected_words =
      reinterpret_cast<const int32_t*>(data->output_data);
  for (int i = 0; i < num_words; i++) {
    if (arena_words[i] != expected_words[i]) {
      diff_count++;
      if (diff_count == 1) {
        first_diff = i;
      }
    }
  }

  if (diff_count == 0) {
    printf("OK - output identical to golden output\n");
  } else {
    printf("FAIL - %d differences, first at word %d\n", diff_count, first_diff);
    printf("actual:\n");
    dump_hex(arena_words + first_diff, 16);
    printf("expected:\n");
    dump_hex(expected_words + first_diff, 16);
  }
}
