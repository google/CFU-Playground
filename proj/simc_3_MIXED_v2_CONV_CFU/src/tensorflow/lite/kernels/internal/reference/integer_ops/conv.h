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

#include <algorithm>

#include "cfu.h"
#include "perf.h"
#include "playground_util/print_params.h"
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/portable_tensor_utils.h"

#ifndef CFU_CONV1d_V3_PARAMS
#define CFU_CONV1d_V3_PARAMS

  #define CFU_INITIALIZE 0
  #define CFU_WRITE_TO_INPUT_BUFFER 1
  #define CFU_WRITE_TO_KERNEL_BUFFER 2
  #define CFU_READ_OUTPUT_BUFFER 3
  #define CFU_START_COMPUTATION 4
  #define CFU_READ_INPUT_BUFFER 5
  #define CFU_READ_KERNEL_BUFFER 6
  #define CFU_SET_BIAS 7
  #define CFU_SET_INPUT_OFFSET 8
#endif // CFU_CONV1d_V3_PARAMS


namespace tflite {
namespace reference_integer_ops {

// Fixed-point per-channel-quantization convolution reference kernel.
inline void ConvPerChannel(
    const ConvParams& params, const int32_t* output_multiplier,
    const int32_t* output_shift, const RuntimeShape& input_shape,
    const int8_t* input_data, const RuntimeShape& filter_shape,
    const int8_t* filter_data, const RuntimeShape& bias_shape,
    const int32_t* bias_data, const RuntimeShape& output_shape,
    int8_t* output_data) {
  // Get parameters.
  // print_conv_params(params, input_shape, filter_shape, output_shape);
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  (void) input_offset;

  // int32_t ret_input_offset = cfu_op0(3, input_offset, 0);
  // printf("ret input offset: %ld\n", ret_input_offset);
  // (void)input_offset;   // Can be unused if I replace de-facto constant parameters with constant

  const int stride_width = 1; (void) stride_width;
  // const int stride_width = params.stride_width;

  const int stride_height = 1; (void) stride_height;
  // const int stride_height = params.stride_height;

  const int dilation_width_factor = 1; (void) dilation_width_factor;
  // const int dilation_width_factor = params.dilation_width_factor;
  
  const int dilation_height_factor = 1; (void) dilation_height_factor;
  // const int dilation_height_factor = params.dilation_height_factor;
  
  const int pad_width = 3; (void) pad_width;
  // const int pad_width = params.padding_values.width;

  const int pad_height = 0; (void) pad_height;
  // const int pad_height = params.padding_values.height;
  
  const int32_t output_offset = -128;
  // const int32_t output_offset = params.output_offset;


  // Set min and max value of the output.
  const int32_t output_activation_min = -128;
  // const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = 127;
  // const int32_t output_activation_max = params.quantized_activation_max;

  // Consistency check.
  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0); (void) batches;
  const int input_depth = input_shape.Dims(3);
  // printf("Input depth: %d\n", input_depth);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int input_height = 1; (void) input_height;
  // const int input_height = input_shape.Dims(1);

  const int input_width = input_shape.Dims(2);

  // const int filter_height = 8;
  const int filter_height = 1; (void) filter_height;
  // const int filter_height = filter_shape.Dims(1);

  // const int filter_width = filter_shape.Dims(2);
  const int filter_width = 8;

  const int filter_input_depth = filter_shape.Dims(3);
  // const int groups = input_depth / filter_input_depth;
  const int groups = 1; (void) groups;
  
  TFLITE_DCHECK_EQ(input_depth % filter_input_depth, 0);
  const int filters_per_group = output_depth / groups; (void)filters_per_group;

  const int output_height = 1; (void) output_height;
  // const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);

  // Convolution with CFU
  // Initialize CFU
  cfu_op0(CFU_INITIALIZE, 0, 0);
  // Set input offset
  cfu_op0(CFU_SET_INPUT_OFFSET, input_offset, 0);

  // Copy input to the buffer
  uint32_t input_buffer_address = 4 * filter_input_depth; // because of paddings
  for (int in_x = 0; in_x < input_width; ++in_x) {
    for (int in_channel = 0; in_channel < filter_input_depth; in_channel += 4, input_buffer_address+=4) {
      int32_t input_val = *(uint32_t*) input_data + Offset(input_shape, 0, 0, in_x, in_channel);
      cfu_op0(CFU_WRITE_TO_INPUT_BUFFER, input_buffer_address, input_val);
    }
  }

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel to the buffer
    uint32_t kernel_buffer_address = 0;
    for (int filter_x = 0; filter_x <= filter_width; ++filter_x) {
      for (int in_channel = 0; in_channel < filter_input_depth; in_channel += 4, kernel_buffer_address+=4) {
        int32_t filter_val = *(uint32_t*) filter_data + Offset(filter_shape, out_channel, 0, filter_x, in_channel);
        cfu_op0(CFU_WRITE_TO_KERNEL_BUFFER, kernel_buffer_address, filter_val);
      }
    }

    // Set bias
    if (bias_data) {
      cfu_op0(CFU_SET_BIAS, bias_data[out_channel], 0);
    }

    // Start computation
    cfu_op0(CFU_START_COMPUTATION, 0, 0);

    // Copy output from the output buffer
    for (int out_x = 0; out_x < output_width; out_x += 4) { 
      uint32_t acc4 = cfu_op0(CFU_READ_OUTPUT_BUFFER, out_x, 0);
      for (int i = 0; i < 4; ++i) {
        int32_t acc = ((int8_t *) &acc4)[i];
        acc = MultiplyByQuantizedMultiplier(acc, output_multiplier[out_channel], output_shift[out_channel]);
        acc += output_offset;
        acc = std::max(acc, output_activation_min);
        acc = std::min(acc, output_activation_max);
        output_data[Offset(output_shape, 0, 0, out_x, out_channel)] = static_cast<int8_t>(acc);
      }
    }
  }

  // // Original convolution code
  // for (int batch = 0; batch < batches; ++batch) {
  //   for (int out_y = 0; out_y < output_height; ++out_y) {
  //     const int in_y_origin = (out_y * stride_height) - pad_height;
  //     for (int out_x = 0; out_x < output_width; ++out_x) {
  //       const int in_x_origin = (out_x * stride_width) - pad_width;
  //       for (int out_channel = 0; out_channel < output_depth; ++out_channel) {

  //         auto group = out_channel / filters_per_group;
  //         int32_t acc = 0;
  //         for (int filter_y = 0; filter_y < filter_height; ++filter_y) {
  //           const int in_y = in_y_origin + dilation_height_factor * filter_y;
  //           for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
  //             const int in_x = in_x_origin + dilation_width_factor * filter_x;

  //             // Zero padding by omitting the areas outside the image.
  //             const bool is_point_inside_image =
  //                 (in_x >= 0) && (in_x < input_width) && (in_y >= 0) &&
  //                 (in_y < input_height);

  //             if (!is_point_inside_image) {
  //               continue;
  //             }

  //             // DEFAULT IMPLEMENTATION
  //             for (int in_channel = 0; in_channel < filter_input_depth;
  //                  ++in_channel) {
  //               int32_t input_val =
  //                   input_data[Offset(input_shape, batch, in_y, in_x,
  //                                     in_channel + group * filter_input_depth)];
  //               int32_t filter_val = filter_data[Offset(
  //                   filter_shape, out_channel, filter_y, filter_x, in_channel)];
  //               acc += filter_val * (input_val + input_offset);
  //             }

  //           }
  //         }

  //         if (bias_data) {
  //           acc += bias_data[out_channel];
  //         }
  //         acc = MultiplyByQuantizedMultiplier(
  //             acc, output_multiplier[out_channel], output_shift[out_channel]);
  //         acc += output_offset;
  //         acc = std::max(acc, output_activation_min);
  //         acc = std::min(acc, output_activation_max);
  //         output_data[Offset(output_shape, batch, out_y, out_x, out_channel)] =
  //             static_cast<int8_t>(acc);
  //       }
  //     }
  //   }
  // }


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
