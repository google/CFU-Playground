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

#include "print_params.h"

const char *to_string(tflite::PaddingType type)
{
  switch (type)
  {
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

void print_shape(const tflite::RuntimeShape &shape)
{
  if (shape.DimensionsCount() != 4)
  {
    puts("*ERR* shape dims should be 4");
  }
  printf("%ld, %ld, %ld, %ld, ", shape.Dims(0), shape.Dims(1), shape.Dims(2), shape.Dims(3));
}

// Format is:
// "padding_type", "padding_width", "padding_height", "padding_width_offset", "padding_height_offset",
// "stride_width", "stride_height", "dilation_width_factor", "dilation_height_factor",
// "input_offset", "weights_offset", "output_offset", "output_multiplier", "output_shift",
// "quantized_activation_min", "quantized_activation_max"
// "input_batches", "input_height", "input_width", "input_depth",
// "filter_output_depth", "filter_height", "filter_width", "filter_input_depth",
// "output_batches", "output_height", "output_width", "output_depth",

void print_conv_params(
    const tflite::ConvParams &params,
    const tflite::RuntimeShape &input_shape,
    const tflite::RuntimeShape &filter_shape,
    const tflite::RuntimeShape &output_shape)
{
  printf("%s, ", to_string(params.padding_type));
  auto &padding = params.padding_values;
  printf("%d, %d, %d, %d, ", padding.width, padding.height, padding.width_offset, padding.height_offset);
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
// "padding_type", "padding_width", "padding_height", "padding_width_offset", "padding_height_offset",
// "stride_width", "stride_height", "dilation_width_factor", "dilation_height_factor", "depth_multiplier"
// "input_offset", "weights_offset", "output_offset", "output_multiplier", "output_shift",
// "quantized_activation_min", "quantized_activation_max"
// "input_batches", "input_height", "input_width", "input_depth",
// "filter_output_depth", "filter_height", "filter_width", "filter_input_depth",
// "output_batches", "output_height", "output_width", "output_depth",

void print_depthwise_params(
    const tflite::DepthwiseParams &params,
    const tflite::RuntimeShape &input_shape,
    const tflite::RuntimeShape &filter_shape,
    const tflite::RuntimeShape &output_shape)
{
  printf("%s, ", to_string(params.padding_type));
  auto &padding = params.padding_values;
  printf("%d, %d, %d, %d, ", padding.width, padding.height, padding.width_offset, padding.height_offset);
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
