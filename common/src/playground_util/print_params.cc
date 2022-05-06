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

#ifndef SKIP_TFLM

#include "print_params.h"

#include <cstdio>

static const char* to_string(tflite::PaddingType type) {
  switch (type) {
    case (tflite::PaddingType::kSame):
      return "kSame";
    case (tflite::PaddingType::kValid):
      return "kValid";
    case (tflite::PaddingType::kNone):
      return "kNone";
    default:
      return "UNKNOWN";
  }
}

static const char* to_string(tflite::BroadcastableOpCategory category) {
  switch (category) {
    case (tflite::BroadcastableOpCategory::kNone):
      return "kNone";
    case (tflite::BroadcastableOpCategory::kNonBroadcast):
      return "kNonBroadcast";
    case (tflite::BroadcastableOpCategory::kFirstInputBroadcastsFast):
      return "kFirstInputBroadcastsFast";
    case (tflite::BroadcastableOpCategory::kSecondInputBroadcastsFast):
      return "kSecondInputBroadcastsFast";
    case (tflite::BroadcastableOpCategory::kGenericBroadcast):
      return "kGenericBroadcast";
    default:
      return "UNKNOWN";
  }
}

static void print_shape(const tflite::RuntimeShape& shape) {
  if (shape.DimensionsCount() == 0) {
    printf("*, *, *, *, ");
    return;
  } else if (shape.DimensionsCount() != 4) {
    printf("*ERR* shape dims should be 4, but are %ld\n",
           shape.DimensionsCount());
  }
  printf("%ld, %ld, %ld, %ld, ", shape.Dims(0), shape.Dims(1), shape.Dims(2),
         shape.Dims(3));
}

// Format is:
// "padding_type", "padding_width", "padding_height", "padding_width_offset",
// "padding_height_offset", "stride_width", "stride_height",
// "dilation_width_factor", "dilation_height_factor", "input_offset",
// "weights_offset", "output_offset", "output_multiplier", "output_shift",
// "quantized_activation_min", "quantized_activation_max",
// "input_batches", "input_height", "input_width", "input_depth",
// "filter_output_depth", "filter_height", "filter_width", "filter_input_depth",
// "output_batches", "output_height", "output_width", "output_depth",

void print_conv_params(const tflite::ConvParams& params,
                       const tflite::RuntimeShape& input_shape,
                       const tflite::RuntimeShape& filter_shape,
                       const tflite::RuntimeShape& output_shape) {
  printf("%s, ", to_string(params.padding_type));
  auto& padding = params.padding_values;
  printf("%d, %d, %d, %d, ", padding.width, padding.height,
         padding.width_offset, padding.height_offset);
  printf("%d, ", params.stride_width);
  printf("%d, ", params.stride_height);
  printf("%d, ", params.dilation_width_factor);
  printf("%d, ", params.dilation_height_factor);
  printf("%ld, ", params.input_offset);
  printf("%ld, ", params.weights_offset);
  printf("%ld, ", params.output_offset);
  printf("%ld, ", params.output_multiplier);
  printf("%d, ", params.output_shift);
  printf("%ld, ", params.quantized_activation_min);
  printf("%ld, ", params.quantized_activation_max);
  print_shape(input_shape);
  print_shape(filter_shape);
  print_shape(output_shape);
  printf("\n");
}

// Format is:
// "padding_type", "padding_width", "padding_height", "padding_width_offset",
// "padding_height_offset", "stride_width", "stride_height",
// "dilation_width_factor", "dilation_height_factor", "depth_multiplier",
// "input_offset", "weights_offset", "output_offset", "output_multiplier",
// "output_shift", "quantized_activation_min", "quantized_activation_max",
// "input_batches", "input_height", "input_width", "input_depth",
// "filter_output_depth", "filter_height", "filter_width", "filter_input_depth",
// "output_batches", "output_height", "output_width", "output_depth",

void print_depthwise_params(const tflite::DepthwiseParams& params,
                            const tflite::RuntimeShape& input_shape,
                            const tflite::RuntimeShape& filter_shape,
                            const tflite::RuntimeShape& output_shape) {
  printf("%s, ", to_string(params.padding_type));
  auto& padding = params.padding_values;
  printf("%d, %d, %d, %d, ", padding.width, padding.height,
         padding.width_offset, padding.height_offset);
  printf("%d, ", params.stride_width);
  printf("%d, ", params.stride_height);
  printf("%d, ", params.dilation_width_factor);
  printf("%d, ", params.dilation_height_factor);
  printf("%d, ", params.depth_multiplier);
  printf("%ld, ", params.input_offset);
  printf("%ld, ", params.weights_offset);
  printf("%ld, ", params.output_offset);
  printf("%ld, ", params.output_multiplier);
  printf("%d, ", params.output_shift);
  printf("%ld, ", params.quantized_activation_min);
  printf("%ld, ", params.quantized_activation_max);
  print_shape(input_shape);
  print_shape(filter_shape);
  print_shape(output_shape);
  printf("\n");
}

// Format is:
// "op_name", "broadcast_category", "input1_offset", "input2_offset",
// "output_offset", "output_multiplier", "output_shift",
// "left_shift",
// "input1_multiplier", "input1_shift", "input2_multiplier", "input2_shift",
// "quantized_activation_min", "quantized_activation_max",
// "broadcast_shape0", "broadcast_shape1", "broadcast_shape2",
// "broadcast_shape3", "broadcast_shape4" "input1_batches", "input1_height",
// "input1_width", "input1_depth", "input2_batches", "input2_height",
// "input2_width", "input2_depth", "output_batches", "output_height",
// "output_width", "output_depth",
void print_arithmetic_params(const char* op_name,
                             const tflite::ArithmeticParams& params,
                             const tflite::RuntimeShape& input1_shape,
                             const tflite::RuntimeShape& input2_shape,
                             const tflite::RuntimeShape& output_shape) {
  printf("%s, ", op_name);
  printf("%s, ", to_string(params.broadcast_category));
  printf("%ld, ", params.input1_offset);
  printf("%ld, ", params.input2_offset);
  printf("%ld, ", params.output_offset);
  printf("%ld, ", params.output_multiplier);
  printf("%d, ", params.output_shift);
  printf("%d, ", params.left_shift);
  printf("%ld, ", params.input1_multiplier);
  printf("%d, ", params.input1_shift);
  printf("%ld, ", params.input2_multiplier);
  printf("%d, ", params.input2_shift);
  printf("%ld, ", params.quantized_activation_min);
  printf("%ld, ", params.quantized_activation_max);
  printf("%d, ", params.broadcast_shape[0]);
  printf("%d, ", params.broadcast_shape[1]);
  printf("%d, ", params.broadcast_shape[2]);
  printf("%d, ", params.broadcast_shape[3]);
  printf("%d, ", params.broadcast_shape[4]);
  print_shape(input1_shape);
  print_shape(input2_shape);
  print_shape(output_shape);
  printf("\n");
}

void print_int32_array(const int32_t* data, size_t count) {
  // Print 8 numbers per line
  for (size_t i = 0; i < count; i++) {
    printf("%10ld, ", data[i]);
    if (i % 8 == 7) {
      printf("\n");
    }
  }
  /// Final EOL, if needed
  if ((count - 1) % 8 == 7) {
    printf("\n");
  }
}

#endif
