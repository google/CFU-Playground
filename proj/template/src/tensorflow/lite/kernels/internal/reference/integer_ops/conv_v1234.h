// Legacy for the most part
#pragma once

#include "cfu_utils.h"
#include "common.h"
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/portable_tensor_utils.h"

namespace tflite {
namespace reference_integer_ops {

inline void ConvPerChannelCFUSoftware4(const ConvParams& params,
                                       const int32_t* output_multiplier,
                                       const int32_t* output_shift,
                                       const RuntimeShape& input_shape,
                                       const int8_t* input_data,
                                       const RuntimeShape& filter_shape,
                                       const int8_t* filter_data,
                                       const RuntimeShape& bias_shape,
                                       const int32_t* bias_data,
                                       const RuntimeShape& output_shape,
                                       int8_t* output_data) {
  // static int call = 0;
  // Initialize cfu
  cfu_op0(0, 0, 0);

  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  cfu_op0(20, 0, input_offset);

  const int pad_width = 3;
  (void)pad_width;

  const int32_t output_offset = -128;
  cfu_op0(21, 0, output_offset);
  const int32_t output_activation_min = -128;
  cfu_op0(22, 0, output_activation_min);
  const int32_t output_activation_max = 127;
  cfu_op0(23, 0, output_activation_max);

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  cfu_op0(24, 0, output_depth);

  const int input_width = input_shape.Dims(2);
  cfu_op0(25, 0, input_width);

  const int filter_width = 8;
  (void)filter_width;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(26, 0, input_depth);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  // Copy input
  for (int in_x = 0; in_x < input_width; ++in_x) {
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      int addr = in_x * input_depth + in_channel;
      cfu_op0(10, addr, input_data[addr]);
    }
  }

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy output_multiplier, output_shift, bias
    cfu_op0(28, 0, output_multiplier[out_channel]);
    cfu_op0(29, 0, output_shift[out_channel]);
    cfu_op0(27, 0, bias_data[out_channel]);

    // Copy kernel
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(11, kernel_x * input_depth + in_channel, filter_data[addr]);
      }
    }

    // Start Convolution
    cfu_op0(40, 0, 0);

    for (int out_x = 0; out_x < output_width; ++out_x) {
      int addr    = out_x * output_depth + out_channel;
      int32_t acc = static_cast<int32_t>(cfu_op0(12, out_x, 0));
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc = std::max(acc, output_activation_min);
      acc = std::min(acc, output_activation_max);

      output_data[addr] = acc;
    }
    // Zero out output buffer
    cfu_op0(15, 0, 0);
  }
}

inline void ConvPerChannelCFUSoftware3(const ConvParams& params,
                                       const int32_t* output_multiplier,
                                       const int32_t* output_shift,
                                       const RuntimeShape& input_shape,
                                       const int8_t* input_data,
                                       const RuntimeShape& filter_shape,
                                       const int8_t* filter_data,
                                       const RuntimeShape& bias_shape,
                                       const int32_t* bias_data,
                                       const RuntimeShape& output_shape,
                                       int8_t* output_data) {
  // static int call = 0;
  // Initialize cfu
  cfu_op0(0, 0, 0);

  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  cfu_op0(7, input_offset, 0);

  const int pad_width = 3;
  (void)pad_width;

  const int32_t output_offset = -128;
  cfu_op0(8, output_offset, 0);
  const int32_t output_activation_min = -128;
  cfu_op0(9, output_activation_min, 0);
  const int32_t output_activation_max = 127;
  cfu_op0(10, output_activation_max, 0);

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  cfu_op0(11, output_depth, 0);

  const int input_width = input_shape.Dims(2);
  cfu_op0(12, input_width, 0);

  const int filter_width = 8;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(13, input_depth, 0);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  // Copy input
  for (int in_x = 0; in_x < input_width; ++in_x) {
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      int addr = in_x * input_depth + in_channel;
      cfu_op0(1, addr, input_data[addr]);
    }
  }

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy output_multiplier, output_shift, bias
    cfu_op0(15, output_multiplier[out_channel], 0);
    cfu_op0(16, output_shift[out_channel], 0);
    cfu_op0(14, bias_data[out_channel], 0);

    // Copy kernel
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(2, kernel_x * input_depth + in_channel, filter_data[addr]);
      }
    }

    // Start Convolution
    cfu_op0(17, 0, 0);

    for (int out_x = 0; out_x < output_width; ++out_x) {
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(cfu_op0(3, out_x, 0));
    }
  }
}

inline void ConvPerChannelCFUSoftware2(const ConvParams& params,
                                       const int32_t* output_multiplier,
                                       const int32_t* output_shift,
                                       const RuntimeShape& input_shape,
                                       const int8_t* input_data,
                                       const RuntimeShape& filter_shape,
                                       const int8_t* filter_data,
                                       const RuntimeShape& bias_shape,
                                       const int32_t* bias_data,
                                       const RuntimeShape& output_shape,
                                       int8_t* output_data) {
  // static int call = 0;
  // Initialize cfu
  cfu_op0(0, 0, 0);

  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  cfu_op0(7, input_offset, 0);

  const int pad_width = 3;
  (void)pad_width;

  const int32_t output_offset = -128;
  cfu_op0(8, output_offset, 0);
  const int32_t output_activation_min = -128;
  cfu_op0(9, output_activation_min, 0);
  const int32_t output_activation_max = 127;
  cfu_op0(10, output_activation_max, 0);

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  cfu_op0(11, output_depth, 0);

  const int input_width = input_shape.Dims(2);
  cfu_op0(12, input_width, 0);

  const int filter_width = 8;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(13, input_depth, 0);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  // Copy output_multiplier, output_shift, bias
  for (int i = 0; i < output_depth; ++i) {
    cfu_op0(15, i, output_multiplier[i]);
    cfu_op0(16, i, output_shift[i]);
    cfu_op0(14, i, bias_data[i]);
  }

  // Copy input
  for (int in_x = 0; in_x < input_width; ++in_x) {
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      int addr = in_x * input_depth + in_channel;
      cfu_op0(1, addr, input_data[addr]);
    }
  }

  // Copy kernel
  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(2, addr, filter_data[addr]);
      }
    }
  }

  // Start Convolution
  cfu_op0(17, 0, 0);

  // Copy data to the output
  for (int out_x = 0; out_x < output_width; ++out_x) {
    for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(cfu_op0(3, addr, 0));
    }
  }
}

// Doesn't work
inline void ConvPerChannelCFUSoftware1(const ConvParams& params,
                                       const int32_t* output_multiplier,
                                       const int32_t* output_shift,
                                       const RuntimeShape& input_shape,
                                       const int8_t* input_data,
                                       const RuntimeShape& filter_shape,
                                       const int8_t* filter_data,
                                       const RuntimeShape& bias_shape,
                                       const int32_t* bias_data,
                                       const RuntimeShape& output_shape,
                                       int8_t* output_data) {
  // Get parameters.
  // print_conv_params(params, input_shape, filter_shape, output_shape);
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  (void)input_offset;

  const int stride_width = 1;
  (void)stride_width;
  // const int stride_width = params.stride_width;

  const int stride_height = 1;
  (void)stride_height;
  // const int stride_height = params.stride_height;

  const int dilation_width_factor = 1;
  (void)dilation_width_factor;
  // const int dilation_width_factor = params.dilation_width_factor;

  const int dilation_height_factor = 1;
  (void)dilation_height_factor;
  // const int dilation_height_factor = params.dilation_height_factor;

  const int pad_width = 3;
  (void)pad_width;
  // const int pad_width = params.padding_values.width;

  const int pad_height = 0;
  (void)pad_height;
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
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  (void)batches;
  const int input_depth = input_shape.Dims(3);
  // printf("Input depth: %d\n", input_depth);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int input_height = 1;
  (void)input_height;
  // const int input_height = input_shape.Dims(1);

  const int input_width = input_shape.Dims(2);

  // const int filter_height = 8;
  const int filter_height = 1;
  (void)filter_height;
  // const int filter_height = filter_shape.Dims(1);

  // const int filter_width = filter_shape.Dims(2);
  const int filter_width = 8;

  const int filter_input_depth = filter_shape.Dims(3);
  // const int groups = input_depth / filter_input_depth;
  const int groups = 1;
  (void)groups;

  TFLITE_DCHECK_EQ(input_depth % filter_input_depth, 0);
  const int filters_per_group = output_depth / groups;
  (void)filters_per_group;

  const int output_height = 1;
  (void)output_height;
  // const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);

  // Convolution with CFU
  // Initialize CFU
  cfu_op0(CFU_INITIALIZE, 0, 0);
  // Set input offset
  cfu_op0(CFU_SET_INPUT_OFFSET, input_offset, 0);

// Copy input to the buffer
  uint32_t max_input_channels = 128;
  for (int in_x = 0; in_x < input_width; ++in_x) {
    uint32_t input_buffer_address = (4 + in_x) * max_input_channels;  // +4 because of paddings
    for (int in_channel = 0; in_channel < filter_input_depth;
         in_channel += 1, input_buffer_address += 1) {
      int8_t input_val = input_data[Offset(input_shape, 0, 0, in_x, in_channel)];
      cfu_op0(CFU_WRITE_TO_INPUT_BUFFER, input_buffer_address, input_val);
    }
  }


  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel to the buffer
    for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
      uint32_t kernel_buffer_address = filter_x * max_input_channels;
      for (int in_channel = 0; in_channel < filter_input_depth;
           in_channel += 1, kernel_buffer_address += 1) {
        int8_t filter_val = filter_data[Offset(filter_shape, out_channel, 0, filter_x, in_channel)];
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
    for (int out_x = 0; out_x < output_width; out_x += 1) {
      int32_t acc = cfu_op0(CFU_READ_OUTPUT_BUFFER, out_x, 0);
      // if (out_x == 0)
      //   printf("acc = %ld\n", acc);
      acc = MultiplyByQuantizedMultiplier(acc, output_multiplier[out_channel],
                                          output_shift[out_channel]);
      acc += output_offset;
      acc = std::max(acc, output_activation_min);
      acc = std::min(acc, output_activation_max);
      output_data[Offset(output_shape, 0, 0, out_x, out_channel)] = static_cast<int8_t>(acc);
      // if (out_x == 0)
      //   printf("quant acc = %ld\n", acc);
    }
  }

  // printf("Output: \n");
  // for (size_t x = 0; x < 10; ++x) {
  //   for (size_t out_c = 0; out_c < 10; ++out_c) {
  //     int offset = Offset(output_shape, 0, 0, x, out_c);
  //     printf("output[%d][%d] = %d, offset = %d\n", x, out_c, output_data[offset], offset);
  //   }
  // }

  // abort();
}

// First attempty trying to write verilog cfu immediately
inline void ConvPerChannelCFU(const ConvParams& params,
                              const int32_t* output_multiplier,
                              const int32_t* output_shift,
                              const RuntimeShape& input_shape,
                              const int8_t* input_data,
                              const RuntimeShape& filter_shape,
                              const int8_t* filter_data,
                              const RuntimeShape& bias_shape,
                              const int32_t* bias_data,
                              const RuntimeShape& output_shape,
                              int8_t* output_data) {
  // Get parameters.
  // print_conv_params(params, input_shape, filter_shape, output_shape);
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  (void)input_offset;

  const int stride_width = 1;
  (void)stride_width;
  // const int stride_width = params.stride_width;

  const int stride_height = 1;
  (void)stride_height;
  // const int stride_height = params.stride_height;

  const int dilation_width_factor = 1;
  (void)dilation_width_factor;
  // const int dilation_width_factor = params.dilation_width_factor;

  const int dilation_height_factor = 1;
  (void)dilation_height_factor;
  // const int dilation_height_factor = params.dilation_height_factor;

  const int pad_width = 3;
  (void)pad_width;
  // const int pad_width = params.padding_values.width;

  const int pad_height = 0;
  (void)pad_height;
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
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  (void)batches;
  const int input_depth = input_shape.Dims(3);
  // printf("Input depth: %d\n", input_depth);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int input_height = 1;
  (void)input_height;
  // const int input_height = input_shape.Dims(1);

  const int input_width = input_shape.Dims(2);

  // const int filter_height = 8;
  const int filter_height = 1;
  (void)filter_height;
  // const int filter_height = filter_shape.Dims(1);

  // const int filter_width = filter_shape.Dims(2);
  const int filter_width = 8;

  const int filter_input_depth = filter_shape.Dims(3);
  // const int groups = input_depth / filter_input_depth;
  const int groups = 1;
  (void)groups;

  TFLITE_DCHECK_EQ(input_depth % filter_input_depth, 0);
  const int filters_per_group = output_depth / groups;
  (void)filters_per_group;

  const int output_height = 1;
  (void)output_height;
  // const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);

  // Convolution with CFU
  // Initialize CFU
  cfu_op0(CFU_INITIALIZE, 0, 0);
  // Set input offset
  cfu_op0(CFU_SET_INPUT_OFFSET, input_offset, 0);

  uint32_t max_input_channels = 128;
  uint32_t counter            = 0;
  // Copy input to the buffer
  for (int in_x = 0; in_x < input_width; ++in_x) {
    uint32_t input_buffer_address = (4 + in_x) * max_input_channels;
    for (int in_channel = 0; in_channel < filter_input_depth;
         in_channel += 4, input_buffer_address += 4) {
      // printf("%p - %d\n", input_data + Offset(input_shape, 0, 0, in_x, in_channel),
      // Offset(input_shape, 0, 0, in_x, in_channel));
      const int8_t* input_vals = &input_data[Offset(input_shape, 0, 0, in_x, in_channel)];
      uint32_t value4;
      if (filter_input_depth == 2) {
        uint16_t value_16      = *(uint16_t*)input_vals;
        uint16_t* value_ptr_16 = (uint16_t*)&value4;
        value_ptr_16[0]        = value_16;
        value_ptr_16[1]        = 0;
      } else {
        value4 = *(uint32_t*)input_vals;
      }
      cfu_op0(CFU_WRITE_TO_INPUT_BUFFER, input_buffer_address, value4);
      ++counter;
    }
  }

  // printf("Input[:20]: \n");
  // for (size_t i = 0; i < 20; ++i) {
  //   printf("input[%d] = %d\n", i, input_data[i]);
  //   uint32_t addr = (4 + i / 2) * max_input_channels;
  //   uint32_t read_input4 = cfu_op0(CFU_READ_INPUT_BUFFER, addr, 0);
  //   int8_t *read_input1 = (int8_t *) &read_input4;
  //   if (i % 2)
  //     printf("input_buffer[%ld] = %d\n", addr, read_input1[1]);
  //   else
  //     printf("input_buffer[%ld] = %d\n", addr, read_input1[0]);
  // }

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel to the buffer
    for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
      uint32_t kernel_buffer_address = filter_x * max_input_channels;
      for (int in_channel = 0; in_channel < filter_input_depth;
           in_channel += 4, kernel_buffer_address += 4) {
        const int8_t* filter_vals =
            &filter_data[Offset(filter_shape, out_channel, 0, filter_x, in_channel)];
        int32_t value4;
        if (filter_input_depth == 2) {
          uint16_t filter_vals_16 = *(uint16_t*)filter_vals;
          uint16_t* value_ptr_16  = (uint16_t*)&value4;
          value_ptr_16[0]         = filter_vals_16;
          value_ptr_16[1]         = 0;
        } else {
          value4 = *(uint32_t*)filter_vals;
        }

        cfu_op0(CFU_WRITE_TO_KERNEL_BUFFER, kernel_buffer_address, value4);
      }
    }

    // printf("\n\nm=%d, Kernel[:8]: \n", out_channel);
    // const int8_t *cur_filter_data = &filter_data[Offset(filter_shape, out_channel, 0, 0, 0)];
    // for (size_t i = 0; i < 16; ++i) {
    //   printf("kernel[%d] => %d\n", i, cur_filter_data[i]);
    //   uint32_t addr = (i / 2) * max_input_channels;
    //   uint32_t read_kernel4 = cfu_op0(CFU_READ_KERNEL_BUFFER, addr, 0);
    //   int8_t *read_kernel1 = (int8_t *) &read_kernel4;
    //   if (i % 2)
    //     printf("kernel_buffer[%ld] => %d\n", addr, read_kernel1[1]);
    //   else
    //     printf("kernel_buffer[%ld] => %d\n", addr, read_kernel1[0]);
    // }

    // Set bias
    if (bias_data) {
      cfu_op0(CFU_SET_BIAS, bias_data[out_channel], 0);
    }

    // Start computation
    cfu_op0(CFU_START_COMPUTATION, 0, 0);

    // Copy output from the output buffer
    for (int out_x = 0; out_x < output_width; out_x += 1) {
      int32_t acc = cfu_op0(CFU_READ_OUTPUT_BUFFER, out_x, 0);
      if (out_x == 0)
        printf("acc = %ld\n", acc);
      acc = MultiplyByQuantizedMultiplier(acc, output_multiplier[out_channel],
                                          output_shift[out_channel]);
      acc += output_offset;
      acc = std::max(acc, output_activation_min);
      acc = std::min(acc, output_activation_max);
      output_data[Offset(output_shape, 0, 0, out_x, out_channel)] = static_cast<int8_t>(acc);
      if (out_x == 0)
        printf("quant acc = %ld\n", acc);
    }
  }

  // printf("Output: \n");
  // for (size_t x = 0; x < 10; ++x) {
  //   for (size_t out_c = 0; out_c < 10; ++out_c) {
  //     int offset = Offset(output_shape, 0, 0, x, out_c);
  //     printf("output[%d][%d] = %d, offset = %d\n", x, out_c, output_data[offset], offset);
  //   }
  // }

  // abort();
}

}  // namespace reference_integer_ops
}  // namespace tflite