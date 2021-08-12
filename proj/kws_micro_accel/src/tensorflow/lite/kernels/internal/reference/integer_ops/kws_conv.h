/* Copyright 2021 The CFU-Playground Authors
   Copyright 2019 The TensorFlow Authors. All Rights Reserved.

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
#ifndef TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_KWS_CONV_H_
#define TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_KWS_CONV_H_

#include "kws_cfu.h"
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/reference/integer_ops/conv.h"

namespace tflite {
namespace reference_integer_ops {

// Optimized 8 bit quantized convolution for layer 1.
#if defined(OPT_LINK_OPS_IN_SRAM) || defined(ALL_OPTIMIZATIONS)
inline void KwsConvPerChannelLayerOne(const ConvParams&, const int32_t*,
                                      const int32_t*, const RuntimeShape&,
                                      const int8_t*, const RuntimeShape&,
                                      const int8_t*, const RuntimeShape&,
                                      const int32_t*, const RuntimeShape&,
                                      int8_t*)
    __attribute__((always_inline));  // Must be inlined to be in SRAM.
#endif
inline void KwsConvPerChannelLayerOne(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const int32_t* bias_data, const RuntimeShape& output_shape,
    int8_t* output_data) {
  // Get parameters.
  const int stride_width = params.stride_width;
  const int stride_height = params.stride_height;
  const int pad_width = params.padding_values.width;
  const int pad_height = params.padding_values.height;

  // Consistency check.
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int input_height = input_shape.Dims(1);
  const int input_width = input_shape.Dims(2);
  const int filter_height = filter_shape.Dims(1);
  const int filter_width = filter_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);

  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      const int in_y_origin = (out_y * stride_height) - pad_height;
      for (int out_x = 0; out_x < output_width; ++out_x) {
        const int in_x_origin = (out_x * stride_width) - pad_width;
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          int32_t acc = RESET_ACC();
          for (int filter_y = 0; filter_y < filter_height; ++filter_y) {
            const int in_y = in_y_origin + filter_y;
            for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
              const int in_x = in_x_origin + filter_x;

              // Zero padding by omitting the areas outside the image.
              const bool is_point_inside_image =
                  (in_x >= 0) && (in_x < input_width) && (in_y >= 0) &&
                  (in_y < input_height);

              if (!is_point_inside_image) {
                continue;
              }

              int32_t input_val =
                  input_data[Offset(input_shape, batch, in_y, in_x, 0)];
              int32_t filter_val = filter_data[Offset(filter_shape, out_channel,
                                                      filter_y, filter_x, 0)];
              acc = MAC_LAYER_ONE(input_val, filter_val);
            }
          }

          acc += bias_data[out_channel];
          acc = KwsMultiplyByQuantizedMultiplier(
              acc, output_multiplier[out_channel], output_shift[out_channel]);
          output_data[Offset(output_shape, 0, out_y, out_x, out_channel)] =
              static_cast<int8_t>(acc);
        }
      }
    }
  }
}

// Optimized 8 bit quantized convolution for layers 2 through 5.
#if defined(OPT_LINK_OPS_IN_SRAM) || defined(ALL_OPTIMIZATIONS)
inline void KwsConvPerChannel(const ConvParams&, const int32_t*, const int32_t*,
                              const RuntimeShape&, const int8_t*,
                              const RuntimeShape&, const int8_t*,
                              const RuntimeShape&, const int32_t*,
                              const RuntimeShape&, int8_t*)
    __attribute__((always_inline));  // Must be inlined to be in SRAM.
#endif
inline void KwsConvPerChannel(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const int32_t* bias_data, const RuntimeShape& output_shape,
    int8_t* output_data) {
  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  const int stride_width = params.stride_width;
  const int stride_height = params.stride_height;
  const int dilation_width_factor = params.dilation_width_factor;
  const int dilation_height_factor = params.dilation_height_factor;
  const int pad_width = params.padding_values.width;
  const int pad_height = params.padding_values.height;
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
  const int input_depth = MatchingDim(input_shape, 3, filter_shape, 3);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int input_height = input_shape.Dims(1);
  const int input_width = input_shape.Dims(2);
  const int filter_height = filter_shape.Dims(1);
  const int filter_width = filter_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);

  if (input_depth == 1 && input_offset == -83 && filter_width == 4 &&
      filter_height == 10) {
    KwsConvPerChannelLayerOne(params, output_multiplier, output_shift,
                              input_shape, input_data, filter_shape,
                              filter_data, bias_shape, bias_data, output_shape,
                              output_data);
    return;
  }
  if (input_depth != 64 || input_offset != 128 || !bias_data ||
      output_offset != -128 || output_activation_max != 127 ||
      output_activation_min != -128 || dilation_height_factor != 1 ||
      dilation_width_factor != 1 || batches != 1 || filter_width != 1 ||
      filter_height != 1 || stride_height != 1 || stride_width != 1 ||
      pad_height != 0 || pad_width != 0) {
    ConvPerChannel(params, output_multiplier, output_shift, input_shape,
                   input_data, filter_shape, filter_data, bias_shape, bias_data,
                   output_shape, output_data);
    return;
  }

  for (int out_y = 0; out_y < output_height; ++out_y) {
    for (int out_x = 0; out_x < output_width; ++out_x) {
      for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
        int32_t acc = RESET_ACC();
        for (int filter_y = 0; filter_y < filter_height; ++filter_y) {
          for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
            // Zero padding by omitting the areas outside the image.
            const bool is_point_inside_image =
                (out_x >= 0) && (out_x < input_width) && (out_y >= 0) &&
                (out_y < input_height);

            if (!is_point_inside_image) {
              continue;
            }

            for (int in_channel = 0; in_channel < 64; in_channel += 4) {
              uint32_t input_val =
                  *((uint32_t*)(input_data + Offset(input_shape, 0, out_y,
                                                    out_x, in_channel)));
              uint32_t filter_val =
                  *((uint32_t*)(filter_data + Offset(filter_shape, out_channel,
                                                     0, 0, in_channel)));
              acc = SIMD_MAC(input_val, filter_val);
            }
          }
        }

        acc += bias_data[out_channel];
        acc = KwsMultiplyByQuantizedMultiplier(
            acc, output_multiplier[out_channel], output_shift[out_channel]);
        output_data[Offset(output_shape, 0, out_y, out_x, out_channel)] =
            static_cast<int8_t>(acc);
      }
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite

#endif  // TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_KWS_CONV_H_
