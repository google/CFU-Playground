/* Copyright 2019 The TensorFlow Authors. All Rights Reserved.

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
#ifndef TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_CONV_H_
#define TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_CONV_H_

#include <stdio.h>

#include <algorithm>

#include "cfu.h"
#include "perf.h"
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/portable_tensor_utils.h"

#define OP_RESET_ACC cfu_op0(0, 1, 1)
#define OP_SET_INPUT_OFFSET(n) cfu_op0(0, 0, n)
#define OP_READ_ACC cfu_op1(0, 1, 0)
#define OP_4MACC(in, filt) cfu_op2(0, in, filt)

static inline int num_bits(int32_t n) {
  int b = 32;
  if (n >= 0) {
    n = -n;
  }
  while (n & (1 << 31)) {
    n = n << 1;
    b--;
  }
  return b + 1;
}

namespace tflite {
namespace reference_integer_ops {
// Fixed-point per-channel-quantization convolution reference kernel.
inline void ConvPerChannelPdti8(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const int32_t* bias_data, const RuntimeShape& output_shape,
    int8_t* output_data) {
  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  const int32_t output_offset = params.output_offset;

  // Set min and max value of the output.
  const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = params.quantized_activation_max;

  // Consistency check.
  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int input_depth = MatchingDim(input_shape, 3, filter_shape, 3);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

#ifdef SHOW_CONV_OUT_WEIGHTS
  // From this we learn
  // -- bias is 17 bits, signed
  // -- multiplier is 31 bits, unsigned / always positive
  // -- -10 <= shift <= -5
  int bbits = 0;
  int ombits = 0;
  int osbits = 0;
  for (int c = 0; c < output_depth; c++) {
    bbits = std::max(bbits, num_bits(bias_data[c]));
    ombits = std::max(ombits, num_bits(output_multiplier[c]));
    osbits = std::max(osbits, num_bits(output_shift[c]));
    printf("%12ld ", bias_data[c]);
    // printf("%12ld ", output_multiplier[c]);
    // if (output_shift[c] > -5 || output_shift[c] < -9)
    //   printf("%12ld ", output_shift[c]);
  }
  puts("");
  printf("Bias, mult, shift: %3d, %3d, %3d\n", bbits, ombits, osbits);
#endif

  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  OP_SET_INPUT_OFFSET(input_offset);

  int32_t* input_data_yx_p = (int32_t*)input_data;
  int8_t* output_data_p = output_data;
  for (int y = 0; y < output_height; ++y) {
    for (int x = 0; x < output_width; ++x) {
      int32_t* filter_data_out_channel_p = (int32_t*)filter_data;
      for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
        // perf_enable_counter(6);
        OP_RESET_ACC;
        int32_t* input_data_p = input_data_yx_p;
        int32_t* filter_data_p = filter_data_out_channel_p;
        // For every output channel, multiply all the input channels by a unique
        // filter value
        for (int i = 0; i < input_depth; i += 8) {
          int32_t in4 = *(input_data_p++);
          int32_t filt4 = *(filter_data_p++);
          OP_4MACC(in4, filt4);
          in4 = *(input_data_p++);
          filt4 = *(filter_data_p++);
          OP_4MACC(in4, filt4);
        }
        // perf_disable_counter(6);
        // perf_enable_counter(7);

        int32_t acc = OP_READ_ACC;
        acc += bias_data[out_channel];
        // acc = MultiplyByQuantizedMultiplier(
        //     acc, output_multiplier[out_channel], output_shift[out_channel]);
        // acc = MultiplyByQuantizedMultiplierSmallerThanOneExp(
        //     acc, output_multiplier[out_channel], output_shift[out_channel]);

        using gemmlowp::RoundingDivideByPOT;
        using gemmlowp::SaturatingRoundingDoublingHighMul;
        int32_t t = cfu_op7(0, acc, output_multiplier[out_channel]);
        acc = cfu_op6(0, t, -output_shift[out_channel]);

        acc += output_offset;
        acc = std::max(acc, output_activation_min);
        acc = std::min(acc, output_activation_max);
        *(output_data_p++) = static_cast<int8_t>(acc);

        // Point to next channel of filter data
        filter_data_out_channel_p += input_depth / 4;
        // perf_disable_counter(7);
      }
      // Point to next "pixel" of input data
      input_data_yx_p += input_depth / 4;
    }
  }
}

// Fixed-point per-channel-quantization convolution reference kernel.
inline void ConvPerChannel(
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

#if SHOW_CONV_PARAMS
  static bool header_done = false;
  if (!header_done) {
    printf("output_activation_min, output_activation_max, ");
    printf(
        "input_offset, stride_width, stride_height, dilation_width_factor, "
        "dilation_height_factor, pad_width, pad_height, output_offset, ");
    printf(
        "input_height, input_width, input_depth, filter_height, filter_width, "
        "output_height, output_width, output_depth, batches, has_bias_data\n");
    header_done = true;
  }
  printf("%ld, ", output_activation_min);
  printf("%ld, ", output_activation_max);
  printf("%ld, ", input_offset);
  printf("%u, ", stride_width);
  printf("%u, ", stride_height);
  printf("%u, ", dilation_width_factor);
  printf("%u, ", dilation_height_factor);
  printf("%u, ", pad_width);
  printf("%u, ", pad_height);
  printf("%4ld, ", output_offset);
  printf("%d, ", input_height);
  printf("%d, ", input_width);
  printf("%d, ", input_depth);
  printf("%d, ", filter_height);
  printf("%d, ", filter_width);
  printf("%d, ", output_height);
  printf("%d, ", output_width);
  printf("%d, ", output_depth);
  printf("%d, ", batches);
  printf("%c", bias_data ? 'Y' : 'N');
  printf("\n");
#endif

  if (output_activation_max == 127 && output_activation_min == -128 &&
      batches == 1 && input_offset == 128 && output_offset == -128 &&
      stride_width == 1 && stride_height == 1 && dilation_width_factor == 1 &&
      dilation_height_factor == 1 && pad_width == 0 && pad_height == 0 &&
      bias_data && filter_height == 1 && filter_width == 1 &&
      input_width == output_width && input_height == output_height &&
      (input_depth & 0x7) == 0 && (output_depth & 0xf) == 0) {
    ConvPerChannelPdti8(params, output_multiplier, output_shift, input_shape,
                        input_data, filter_shape, filter_data, bias_shape,
                        bias_data, output_shape, output_data);
    return;
  }

  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      const int in_y_origin = (out_y * stride_height) - pad_height;
      for (int out_x = 0; out_x < output_width; ++out_x) {
        const int in_x_origin = (out_x * stride_width) - pad_width;
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          int32_t acc = 0;
          for (int filter_y = 0; filter_y < filter_height; ++filter_y) {
            const int in_y = in_y_origin + dilation_height_factor * filter_y;
            for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
              const int in_x = in_x_origin + dilation_width_factor * filter_x;

              // Zero padding by omitting the areas outside the image.
              const bool is_point_inside_image =
                  (in_x >= 0) && (in_x < input_width) && (in_y >= 0) &&
                  (in_y < input_height);

              if (!is_point_inside_image) {
                continue;
              }

              for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
                int32_t input_val = input_data[Offset(input_shape, batch, in_y,
                                                      in_x, in_channel)];
                int32_t filter_val = filter_data[Offset(
                    filter_shape, out_channel, filter_y, filter_x, in_channel)];
                // Accumulate with 32 bits accumulator.
                // In the nudging process during model quantization, we force
                // real value of 0.0 be represented by a quantized value. This
                // guarantees that the input_offset is a int8_t, even though
                // it is represented using int32_t. int32_t += int8_t *
                // (int8_t - int8_t) so the highest value we can get from each
                // accumulation is [-127, 127] * ([-128, 127] -
                // [-128, 127]), which is [-32512, 32512]. log2(32512)
                // = 14.98, which means we can accumulate at least 2^16
                // multiplications without overflow. The accumulator is
                // applied to a filter so the accumulation logic will hold as
                // long as the filter size (filter_y * filter_x * in_channel)
                // does not exceed 2^16, which is the case in all the models
                // we have seen so far.
                // TODO(jianlijianli): Add a check to make sure the
                // accumulator depth is smaller than 2^16.
                acc += filter_val * (input_val + input_offset);
              }
            }
          }

          if (bias_data) {
            acc += bias_data[out_channel];
          }
          acc = MultiplyByQuantizedMultiplier(
              acc, output_multiplier[out_channel], output_shift[out_channel]);
          acc += output_offset;
          acc = std::max(acc, output_activation_min);
          acc = std::min(acc, output_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, out_channel)] =
              static_cast<int8_t>(acc);
        }
      }
    }
  }
}


inline void ConvPerChannelWithPackedInt4Weights(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_input, int8_t* unpacked_filter_data,
    const RuntimeShape& bias_shape, const int32_t* bias_data,
    const RuntimeShape& output_shape, int8_t* output_data) {
  TFLITE_DCHECK(unpacked_filter_data != nullptr);
  tflite::tensor_utils::UnpackDenseInt4IntoInt8(
      filter_input, filter_shape.FlatSize(), unpacked_filter_data);
  ConvPerChannel(params, output_multiplier, output_shift, input_shape,
                 input_data, filter_shape, unpacked_filter_data, bias_shape,
                 bias_data, output_shape, output_data);
}

// Fixed-point per-channel-quantization convolution reference kernel.
// 16-bit data and 8-bit filter
template <typename AccumScalar>
inline void ConvPerChannel(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int16_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const AccumScalar* bias_data, const RuntimeShape& output_shape,
    int16_t* output_data) {
  // Get parameters.
  const int stride_width = params.stride_width;
  const int stride_height = params.stride_height;
  const int dilation_width_factor = params.dilation_width_factor;
  const int dilation_height_factor = params.dilation_height_factor;
  const int pad_width = params.padding_values.width;
  const int pad_height = params.padding_values.height;

  // Set min and max value of the output.
  const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = params.quantized_activation_max;

  // Consistency check.
  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int input_depth = input_shape.Dims(3);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int input_height = input_shape.Dims(1);
  const int input_width = input_shape.Dims(2);
  const int filter_height = filter_shape.Dims(1);
  const int filter_width = filter_shape.Dims(2);
  const int filter_input_depth = filter_shape.Dims(3);
  const int groups = input_depth / filter_input_depth;
  TFLITE_DCHECK_EQ(input_depth % filter_input_depth, 0);
  const int filters_per_group = output_depth / groups;
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      const int in_y_origin = (out_y * stride_height) - pad_height;
      for (int out_x = 0; out_x < output_width; ++out_x) {
        const int in_x_origin = (out_x * stride_width) - pad_width;
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          auto group = out_channel / filters_per_group;
          AccumScalar acc = 0;
          for (int filter_y = 0; filter_y < filter_height; ++filter_y) {
            const int in_y = in_y_origin + dilation_height_factor * filter_y;
            for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
              const int in_x = in_x_origin + dilation_width_factor * filter_x;

              // Zero padding by omitting the areas outside the image.
              const bool is_point_inside_image =
                  (in_x >= 0) && (in_x < input_width) && (in_y >= 0) &&
                  (in_y < input_height);

              if (!is_point_inside_image) {
                continue;
              }

              for (int in_channel = 0; in_channel < filter_input_depth;
                   ++in_channel) {
                int32_t input_val =
                    input_data[Offset(input_shape, batch, in_y, in_x,
                                      in_channel + group * filter_input_depth)];
                int32_t filter_val = filter_data[Offset(
                    filter_shape, out_channel, filter_y, filter_x, in_channel)];
                // Accumulate with 64 bits accumulator.
                // int64_t += int8_t * int16_t so the highest value we can
                // get from each accumulation is [-127, 127] * ([-32768,
                // 32767] -
                // [-32768, 32767]), which is [-8322945, 8322945].
                // log2(8322945) = 22.99.
                acc += filter_val * input_val;
              }
            }
          }
          if (bias_data) {
            acc += bias_data[out_channel];
          }
          int32_t scaled_acc = MultiplyByQuantizedMultiplier(
              acc, output_multiplier[out_channel], output_shift[out_channel]);
          scaled_acc = std::max(scaled_acc, output_activation_min);
          scaled_acc = std::min(scaled_acc, output_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, out_channel)] =
              static_cast<int16_t>(scaled_acc);
        }
      }
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite

#endif  // TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_CONV_H_
