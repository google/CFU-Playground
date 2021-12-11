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

#include "tensorflow/lite/kernels/internal/reference/integer_ops/conv.h"

void test_conv2d(const Conv2DData* data) {
  printf("Testing Conv2D %s\n", data->name);
  // Allocate buffer on stack large enough for largest output in HPS model
  constexpr int buf_size = 128 * 1024;
  int8_t actual_output[buf_size];

  const tflite::RuntimeShape& output_shape =
      *(reinterpret_cast<const tflite::RuntimeShape*>(data->output_shape));
  assert((output_shape.FlatSize() <= buf_size, ""));
  tflite::reference_integer_ops::ConvPerChannel(
      *(reinterpret_cast<const tflite::ConvParams*>(data->params)),
      reinterpret_cast<const int32_t*>(data->output_multiplier),
      reinterpret_cast<const int32_t*>(data->output_shift),
      *(reinterpret_cast<const tflite::RuntimeShape*>(data->input_shape)),
      reinterpret_cast<const int8_t*>(data->input_data),
      *(reinterpret_cast<const tflite::RuntimeShape*>(data->filter_shape)),
      reinterpret_cast<const int8_t*>(data->filter_data),
      *(reinterpret_cast<const tflite::RuntimeShape*>(data->bias_shape)),
      reinterpret_cast<const int32_t*>(data->bias_data), output_shape,
      actual_output);

  // Check for differences with output
  int diff_count = 0;
  int first_diff = 0;
  for (int i = 0; i < output_shape.FlatSize(); i++) {
    if (actual_output[i] != static_cast<int8_t>(data->output_data[i])) {
      diff_count++;
      if (diff_count == 1) {
        first_diff = i;
      }
    }
  }

  if (diff_count == 0) {
    printf("OK - output identical to golden ouput\n");
  } else {
    printf("FAIL - %d differences, first at index %d\n", diff_count,
           first_diff);
  }
}
