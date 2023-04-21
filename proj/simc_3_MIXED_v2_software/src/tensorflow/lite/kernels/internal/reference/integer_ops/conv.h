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

// #ifndef CFU_CONV1d_V3_PARAMS
// #define CFU_CONV1d_V3_PARAMS
// #define CFU_INITIALIZE 0
// #define CFU_WRITE_TO_INPUT_BUFFER 1
// #define CFU_WRITE_TO_KERNEL_BUFFER 2
// #define CFU_READ_OUTPUT_BUFFER 3
// #define CFU_START_COMPUTATION 4
// #define CFU_READ_INPUT_BUFFER 5
// #define CFU_READ_KERNEL_BUFFER 6
// #define CFU_SET_BIAS 7
// #define CFU_SET_INPUT_OFFSET 8
// #endif  // CFU_CONV1d_V3_PARAMS

#ifndef CFU_CONV1d_V8_PARAMS
#define CFU_CONV1d_V8_PARAMS

#define CFU_INITIALIZE 0
#define CFU_WRITE_INPUT_BUFFER 1
#define CFU_WRITE_KERNEL_BUFFER 2
#define CFU_WRITE_INPUT_OFFSET 3
#define CFU_WRITE_INPUT_OUTPUT_WIDTH 4
#define CFU_WRITE_INPUT_DEPTH 5
#define CFU_START_COMPUTATION 6
#define CFU_READ_ACCUMULATOR 7
#define CFU_WRITE_START_FILTER_X 8
#define CFU_FINISHED 9

#endif  // CFU_CONV1d_V8_PARAMS

namespace tflite {
namespace reference_integer_ops {

// #define ConvPerChannel ConvPerChannelVeryOriginal
// #define ConvPerChannel ConvPerChannelOriginal
// #define ConvPerChannel ConvPerChannelCFU
// #define ConvPerChannel ConvPerChannelCFUSoftware1
// #define ConvPerChannel ConvPerChannelCFUSoftware2
// #define ConvPerChannel ConvPerChannelCFUSoftware3
// #define ConvPerChannel ConvPerChannelCFUSoftware4
// #define ConvPerChannel ConvPerChannelCFUHardware5
// #define ConvPerChannel ConvPerChannelCFUHardware6
// #define ConvPerChannel ConvPerChannelCFUHardware7
// #define ConvPerChannel ConvPerChannelCFUHardware8
#define ConvPerChannel ConvPerChannelCFUHardware9
// #define ConvPerChannel ConvPerChannelCFUHardware10
// #define ConvPerChannel ConvPerChannelCFUHardware11
// #define ConvPerChannel ConvPerChannelOriginalSimple
#define DEBUG_PRINTS 1

namespace {
template <typename IntegerType>
inline IntegerType rounding_divide_by_POT(IntegerType x, int exponent) {
  assert(exponent >= 0);
  assert(exponent <= 31);
  const IntegerType mask      = (1ll << exponent) - 1;
  const IntegerType zero      = 0;
  const IntegerType one       = 1;
  const IntegerType remainder = x & mask;
  const IntegerType threshold = (mask >> 1) + (((x < zero) ? ~0 : 0) & one);
  return (x >> exponent) + (((remainder > threshold) ? ~0 : 0) & one);
}

inline std::int32_t saturating_rounding_doubling_high_mul(std::int32_t a, std::int32_t b) {
  bool overflow = a == b && a == std::numeric_limits<std::int32_t>::min();
  std::int64_t a_64(a);
  std::int64_t b_64(b);
  std::int64_t ab_64        = a_64 * b_64;
  std::int32_t nudge        = ab_64 >= 0 ? (1 << 30) : (1 - (1 << 30));
  std::int32_t ab_x2_high32 = static_cast<std::int32_t>((ab_64 + nudge) / (1ll << 31));
  return overflow ? std::numeric_limits<std::int32_t>::max() : ab_x2_high32;
}

inline int32_t multiply_by_quant_mult(int32_t x, int32_t quantized_multiplier, int shift) {
  int left_shift  = shift > 0 ? shift : 0;
  int right_shift = shift > 0 ? 0 : -shift;
  return rounding_divide_by_POT(
      saturating_rounding_doubling_high_mul(x * (1 << left_shift), quantized_multiplier),
      right_shift);
}
}  // namespace

inline void ConvPerChannelCFUHardware11(const ConvParams& params,
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
  cfu_op0(CFU_INITIALIZE, 0, 0);

  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  cfu_op0(CFU_WRITE_INPUT_OFFSET, 0, input_offset);

  // for (int addr = 0; addr < 8 * 128; ++addr) {
  //   cfu_op0(CFU_WRITE_INPUT_BUFFER, addr, -input_offset);
  //   cfu_op0(CFU_WRITE_KERNEL_BUFFER, addr, -input_offset);
  // }

  const int pad_width = 3;
  (void)pad_width;

  const int32_t output_offset         = -128;
  const int32_t output_activation_min = -128;
  const int32_t output_activation_max = 127;

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);

  const int input_width = input_shape.Dims(2);
  cfu_op0(CFU_WRITE_INPUT_OUTPUT_WIDTH, 0, input_width);

  const int filter_width = 8;
  (void)filter_width;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(CFU_WRITE_INPUT_DEPTH, 0, input_depth);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel
    for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(CFU_WRITE_KERNEL_BUFFER, kernel_x * input_depth + in_channel, filter_data[addr]);
        // printf("kernel_buffer[%d] <= %d\n", kernel_x * input_depth + in_channel,
        // filter_data[addr]);
      }
    }

    int input_cur_x = -pad_width;
    // Copy input - first 8 xs
    for (int filter_x = 0; filter_x < 8; ++filter_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);

        // This is required to avoid mod in cfu
        if (input_depth == 2) {
          cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr + 8 * input_depth, value);
        }
      }
      ++input_cur_x;
    }

    int start_filter_x = 0;

    for (int out_x = 0; out_x < output_width; ++out_x) {
      cfu_op0(CFU_WRITE_START_FILTER_X, 0, start_filter_x);
      cfu_op0(CFU_START_COMPUTATION, 0, 0);
      while (!cfu_op0(CFU_FINISHED, 0, 0)) {
      };
      int32_t acc = cfu_op0(CFU_READ_ACCUMULATOR, 0, 0);
      // printf("out_x: %d, acc: %ld\n", out_x, acc);
      // abort();

      if (bias_data) {
        acc += bias_data[out_channel];
      }
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc               = std::max(acc, output_activation_min);
      acc               = std::min(acc, output_activation_max);
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);

      // Copy input
      if (out_x == (output_width - 1)) {
        continue;
      }
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = start_filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);

        // This is required to avoid mod in cfu
        if (input_depth == 2) {
          cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr + 8 * input_depth, value);
        }
      }
      ++input_cur_x;
      start_filter_x = (start_filter_x + 1) % 8;
    }
    // abort();
  }
}

// inline void ConvPerChannelCFUHardware10(const ConvParams& params,
//                                         const int32_t* output_multiplier,
//                                         const int32_t* output_shift,
//                                         const RuntimeShape& input_shape,
//                                         const int8_t* input_data,
//                                         const RuntimeShape& filter_shape,
//                                         const int8_t* filter_data,
//                                         const RuntimeShape& bias_shape,
//                                         const int32_t* bias_data,
//                                         const RuntimeShape& output_shape,
//                                         int8_t* output_data) {
//   // static int call = 0;
//   // Initialize cfu
//   cfu_op0(CFU_INITIALIZE, 0, 0);

//   // Get parameters.
//   const int32_t input_offset = params.input_offset;  // r = s(q - Z)
//   cfu_op0(CFU_WRITE_INPUT_OFFSET, 0, input_offset);

//   // for (int addr = 0; addr < 8 * 128; ++addr) {
//   //   cfu_op0(CFU_WRITE_INPUT_BUFFER, addr, -input_offset);
//   //   cfu_op0(CFU_WRITE_KERNEL_BUFFER, addr, -input_offset);
//   // }

//   const int pad_width = 3;
//   (void)pad_width;

//   const int32_t output_offset         = -128;
//   const int32_t output_activation_min = -128;
//   const int32_t output_activation_max = 127;

//   const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);

//   const int input_width = input_shape.Dims(2);
//   cfu_op0(CFU_WRITE_INPUT_OUTPUT_WIDTH, 0, input_width);

//   const int filter_width = 8;
//   (void)filter_width;

//   const int input_depth = filter_shape.Dims(3);
//   cfu_op0(CFU_WRITE_INPUT_DEPTH, 0, input_depth);

//   // const int output_width = output_shape.Dims(2);
//   const int output_width = input_width;

//   int increase_v = (input_depth == 2) ? 2 : 4;
//   for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
//     // Copy kernel
//     for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
//       for (int in_channel = 0; in_channel < input_depth; in_channel += increase_v) {
//         int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;

//         int32_t filter_value;
//         if (input_depth == 2) {
//           filter_value = static_cast<int32_t>(*reinterpret_cast<int16_t*>(filter_data + addr));
//         } else {
//           filter_value = *reinterpret_cast<int32_t*>(filter_data + addr);
//         }
//         cfu_op0(CFU_WRITE_KERNEL_BUFFER, kernel_x * input_depth + in_channel, filter_value);
//         // printf("kernel_buffer[%d] <= %d\n", kernel_x * input_depth + in_channel,
//         // filter_data[addr]);
//       }
//     }

//     int input_cur_x = -pad_width;
//     // Copy input - first 8 xs
//     for (int filter_x = 0; filter_x < 8; ++filter_x) {
//       for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
//         int buffer_addr = filter_x * input_depth + in_channel;
//         int8_t value    = -input_offset;
//         if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
//           int input_addr = input_cur_x * input_depth + in_channel;
//           value          = input_data[input_addr];
//         }
//         cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);

//         // This is required to avoid mod in cfu
//         if (input_depth == 2) {
//           cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr + 8 * input_depth, value);
//         }
//       }
//       ++input_cur_x;
//     }

//     int start_filter_x = 0;

//     for (int out_x = 0; out_x < output_width; ++out_x) {
//       cfu_op0(CFU_WRITE_START_FILTER_X, 0, start_filter_x);
//       cfu_op0(CFU_START_COMPUTATION, 0, 0);
//       while (!cfu_op0(CFU_FINISHED, 0, 0)) {
//       };
//       int32_t acc = cfu_op0(CFU_READ_ACCUMULATOR, 0, 0);
//       // printf("out_x: %d, acc: %ld\n", out_x, acc);
//       // abort();

//       if (bias_data) {
//         acc += bias_data[out_channel];
//       }
//       acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

//       acc += output_offset;
//       acc               = std::max(acc, output_activation_min);
//       acc               = std::min(acc, output_activation_max);
//       int addr          = out_x * output_depth + out_channel;
//       output_data[addr] = static_cast<int8_t>(acc);

//       // Copy input
//       if (out_x == (output_width - 1)) {
//         continue;
//       }
//       for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
//         int buffer_addr = start_filter_x * input_depth + in_channel;
//         int8_t value    = -input_offset;
//         if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
//           int input_addr = input_cur_x * input_depth + in_channel;
//           value          = input_data[input_addr];
//         }
//         cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);

//         // This is required to avoid mod in cfu
//         if (input_depth == 2) {
//           cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr + 8 * input_depth, value);
//         }
//       }
//       ++input_cur_x;
//       start_filter_x = (start_filter_x + 1) % 8;
//     }
//     // abort();
//   }
// }

inline void ConvPerChannelCFUHardware9(const ConvParams& params,
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
  cfu_op0(CFU_INITIALIZE, 0, 0);

  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  cfu_op0(CFU_WRITE_INPUT_OFFSET, 0, input_offset);

  // for (int addr = 0; addr < 8 * 128; ++addr) {
  //   cfu_op0(CFU_WRITE_INPUT_BUFFER, addr, -input_offset);
  //   cfu_op0(CFU_WRITE_KERNEL_BUFFER, addr, -input_offset);
  // }

  const int pad_width = 3;
  (void)pad_width;

  const int32_t output_offset         = -128;
  const int32_t output_activation_min = -128;
  const int32_t output_activation_max = 127;

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);

  const int input_width = input_shape.Dims(2);
  cfu_op0(CFU_WRITE_INPUT_OUTPUT_WIDTH, 0, input_width);

  const int filter_width = 8;
  (void)filter_width;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(CFU_WRITE_INPUT_DEPTH, 0, input_depth);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel
    for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(CFU_WRITE_KERNEL_BUFFER, kernel_x * input_depth + in_channel, filter_data[addr]);
        // printf("kernel_buffer[%d] <= %d\n", kernel_x * input_depth + in_channel,
        // filter_data[addr]);
      }
    }

    int input_cur_x = -pad_width;
    // Copy input - first 8 xs
    for (int filter_x = 0; filter_x < 8; ++filter_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);

        // This is required to avoid mod in cfu
        if (input_depth == 2) {
          cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr + 8 * input_depth, value);
        }
      }
      ++input_cur_x;
    }

    int start_filter_x = 0;

    for (int out_x = 0; out_x < output_width; ++out_x) {
      cfu_op0(CFU_WRITE_START_FILTER_X, 0, start_filter_x);
      cfu_op0(CFU_START_COMPUTATION, 0, 0);
      while (!cfu_op0(CFU_FINISHED, 0, 0)) {
      };
      int32_t acc = cfu_op0(CFU_READ_ACCUMULATOR, 0, 0);
      // printf("out_x: %d, acc: %ld\n", out_x, acc);
      // abort();

      if (bias_data) {
        acc += bias_data[out_channel];
      }
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc               = std::max(acc, output_activation_min);
      acc               = std::min(acc, output_activation_max);
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);

      // Copy input
      if (out_x == (output_width - 1)) {
        continue;
      }
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = start_filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);

        // This is required to avoid mod in cfu
        if (input_depth == 2) {
          cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr + 8 * input_depth, value);
        }
      }
      ++input_cur_x;
      start_filter_x = (start_filter_x + 1) % 8;
    }
    // abort();
  }
}

inline void ConvPerChannelCFUHardware8(const ConvParams& params,
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
  cfu_op0(CFU_INITIALIZE, 0, 0);
  // Zero out buffers
  for (int addr = 0; addr < 8 * 128; ++addr) {
    cfu_op0(CFU_WRITE_INPUT_BUFFER, addr, 0);
    cfu_op0(CFU_WRITE_KERNEL_BUFFER, addr, 0);
  }

  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  cfu_op0(CFU_WRITE_INPUT_OFFSET, 0, input_offset);

  const int pad_width = 3;
  (void)pad_width;

  const int32_t output_offset         = -128;
  const int32_t output_activation_min = -128;
  const int32_t output_activation_max = 127;

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);

  const int input_width = input_shape.Dims(2);
  cfu_op0(CFU_WRITE_INPUT_OUTPUT_WIDTH, 0, input_width);

  const int filter_width = 8;
  (void)filter_width;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(CFU_WRITE_INPUT_DEPTH, 0, input_depth);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel
    for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(CFU_WRITE_KERNEL_BUFFER, kernel_x * input_depth + in_channel, filter_data[addr]);
        // printf("kernel_buffer[%d] <= %d\n", kernel_x * input_depth + in_channel,
        // filter_data[addr]);
      }
    }

    int input_cur_x = -pad_width;
    // Copy input - first 8 xs
    for (int filter_x = 0; filter_x < 8; ++filter_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);
      }
      ++input_cur_x;
    }

    int start_filter_x = 0;

    for (int out_x = 0; out_x < output_width; ++out_x) {
      cfu_op0(CFU_WRITE_START_FILTER_X, 0, start_filter_x);
      cfu_op0(CFU_START_COMPUTATION, 0, 0);
      while (!cfu_op0(CFU_FINISHED, 0, 0)) {
      };
      int32_t acc = cfu_op0(CFU_READ_ACCUMULATOR, 0, 0);
      // printf("out_x: %d, acc: %ld\n", out_x, acc);
      // abort();

      if (bias_data) {
        acc += bias_data[out_channel];
      }
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc               = std::max(acc, output_activation_min);
      acc               = std::min(acc, output_activation_max);
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);

      // Copy input
      if (out_x == (output_width - 1)) {
        continue;
      }
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = start_filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);
      }
      ++input_cur_x;
      start_filter_x = (start_filter_x + 1) % 8;
    }
    // abort();
  }
}

inline void ConvPerChannelCFUHardware7(const ConvParams& params,
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

  const int32_t output_offset         = -128;
  const int32_t output_activation_min = -128;
  const int32_t output_activation_max = 127;

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);

  const int input_width = input_shape.Dims(2);
  cfu_op0(25, 0, input_width);

  const int filter_width = 8;
  (void)filter_width;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(26, 0, input_depth);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  // Copy input
  // for (int in_x = 0; in_x < input_width; ++in_x) {
  //   for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
  //     int addr = in_x * input_depth + in_channel;
  //     cfu_op0(10, addr, input_data[addr]);
  //   }
  // }

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel
    for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(11, kernel_x * input_depth + in_channel, filter_data[addr]);
        // printf("kernel_buffer[%d] <= %d\n", kernel_x * input_depth + in_channel,
        // filter_data[addr]);
      }
    }

    int input_cur_x = -pad_width;
    // Copy input
    for (int filter_x = 0; filter_x < 8; ++filter_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(10, buffer_addr, value);
      }
      ++input_cur_x;
    }

    int start_filter_x = 0;

    for (int out_x = 0; out_x < output_width; ++out_x) {
      // const int in_x_origin = out_x - pad_width;

      // cfu_op0(42, 0, in_x_origin);
      cfu_op0(44, 0, start_filter_x);
      cfu_op0(41, 0, 0);
      int32_t acc = cfu_op0(43, 0, 0);
      // printf("out_x: %d, acc: %ld\n", out_x, acc);
      // abort();

      if (bias_data) {
        acc += bias_data[out_channel];
      }
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc               = std::max(acc, output_activation_min);
      acc               = std::min(acc, output_activation_max);
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);

      // Copy input
      if (out_x == (output_width - 1)) {
        continue;
      }
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = start_filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(10, buffer_addr, value);
      }
      ++input_cur_x;
      start_filter_x = (start_filter_x + 1) % 8;
    }
    // abort();
  }
}

inline void ConvPerChannelCFUHardware6(const ConvParams& params,
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

  const int32_t output_offset         = -128;
  const int32_t output_activation_min = -128;
  const int32_t output_activation_max = 127;

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);

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
    // Copy kernel
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(11, kernel_x * input_depth + in_channel, filter_data[addr]);
      }
    }
    cfu_op0(27, 0, bias_data[out_channel]);

    for (int out_x = 0; out_x < output_width; ++out_x) {
      const int in_x_origin = out_x - pad_width;

      cfu_op0(42, 0, in_x_origin);
      cfu_op0(41, 0, 0);
      int32_t acc = cfu_op0(43, 0, 0);

      if (bias_data) {
        acc += bias_data[out_channel];
      }
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc               = std::max(acc, output_activation_min);
      acc               = std::min(acc, output_activation_max);
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);
    }
  }
}

inline void ConvPerChannelCFUHardware5(const ConvParams& params,
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
  printf("Done copying input\n");

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(11, kernel_x * input_depth + in_channel, filter_data[addr]);
      }
    }
    cfu_op0(27, 0, bias_data[out_channel]);

    for (int out_x = 0; out_x < output_width; ++out_x) {
      const int in_x_origin = out_x - pad_width;

      cfu_op0(42, 0, in_x_origin);
      cfu_op0(41, 0, 0);
      int32_t acc = cfu_op0(43, 0, 0);

      if (bias_data) {
        acc += bias_data[out_channel];
      }
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc               = std::max(acc, output_activation_min);
      acc               = std::min(acc, output_activation_max);
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);
    }
  }
}

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

// Fixed-point per-channel-quantization convolution reference kernel.
inline void ConvPerChannelOriginalSimple(const ConvParams& params,
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
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)

  const int pad_width = 3;

  const int32_t output_offset         = -128;
  const int32_t output_activation_min = -128;
  const int32_t output_activation_max = 127;

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  const int input_width  = input_shape.Dims(2);
  const int filter_width = 8;
  const int input_depth  = filter_shape.Dims(3);
  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  // input_shape = 1 x 1 x input_width x input_channels
  // kerne_shape = output_channels x 1 x 8 x input_channels
  // output_shaoe = 1 x 1 x output_width x output_channels

  // Original convolution code
  for (int out_x = 0; out_x < output_width; ++out_x) {
    const int in_x_origin = out_x - pad_width;
    for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
      int32_t acc = 0;
      for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
        const int in_x = in_x_origin + filter_x;

        // Zero padding by omitting the areas outside the image.
        const bool is_point_inside_image = (in_x >= 0) && (in_x < input_width);
        if (!is_point_inside_image) {
          continue;
        }

        // DEFAULT IMPLEMENTATION
        for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
          int32_t input_val = input_data[in_x * input_depth + in_channel];
          int32_t filter_val =
              filter_data[out_channel * (8 * input_depth) + filter_x * input_depth + in_channel];

          acc += filter_val * (input_val + input_offset);
        }
      }
      if (bias_data) {
        acc += bias_data[out_channel];
      }
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc               = std::max(acc, output_activation_min);
      acc               = std::min(acc, output_activation_max);
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);
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
#ifdef DEBUG_PRINTS
  printf("================= Start convolution =================\n");
  // printf("Write to input buffer\n");
#endif
  uint32_t max_input_channels = 128;
  for (int in_x = 0; in_x < input_width; ++in_x) {
    uint32_t input_buffer_address = (4 + in_x) * max_input_channels;  // +4 because of paddings
    for (int in_channel = 0; in_channel < filter_input_depth;
         in_channel += 1, input_buffer_address += 1) {
      int8_t input_val = input_data[Offset(input_shape, 0, 0, in_x, in_channel)];
      // #ifdef DEBUG_PRINTS
      //       if (in_x < 10) {
      //         printf("input_buffer[%ld] <= %d\n", input_buffer_address, input_val);
      //       }
      // #endif
      cfu_op0(CFU_WRITE_TO_INPUT_BUFFER, input_buffer_address, input_val);
    }
  }

  // #ifdef DEBUG_PRINTS
  //   printf("Input[:20]: \n");
  //   for (size_t i = 0; i < 20; ++i) {
  //     printf("input[%d] = %d\n", i, input_data[i]);
  //     uint32_t addr     = (4 + i / 2) * max_input_channels + i % 2;
  //     int8_t read_input = (int8_t)cfu_op0(CFU_READ_INPUT_BUFFER, addr, 0);
  //     printf("input_buffer[%ld] => %d\n", addr, read_input);
  //   }
  // #endif

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

    // #ifdef DEBUG_PRINTS
    //     printf("\n\nm=%d, Kernel[:8]: \n", out_channel);
    //     const int8_t *cur_filter_data = &filter_data[Offset(filter_shape, out_channel, 0, 0, 0)];
    //     for (size_t i = 0; i < 16; ++i) {
    //       printf("kernel[%d] => %d\n", i, cur_filter_data[i]);
    //       uint32_t addr = (i / 2) * max_input_channels + i % 2;
    //       int8_t read_kernel = (int8_t) cfu_op0(CFU_READ_KERNEL_BUFFER, addr, 0);
    //       printf("kernel_buffer[%ld] => %d\n", addr, read_kernel);
    //     }
    // #endif

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

// Fixed-point per-channel-quantization convolution reference kernel.
inline void ConvPerChannelOriginal(const ConvParams& params,
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

  // int32_t ret_input_offset = cfu_op0(3, input_offset, 0);
  // printf("ret input offset: %ld\n", ret_input_offset);
  // (void)input_offset;   // Can be unused if I replace de-facto constant parameters with
  // constant

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

  // Original convolution code
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      const int in_y_origin = (out_y * stride_height) - pad_height;
      for (int out_x = 0; out_x < output_width; ++out_x) {
        const int in_x_origin = (out_x * stride_width) - pad_width;
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          auto group  = out_channel / filters_per_group;
          int32_t acc = 0;
          for (int filter_y = 0; filter_y < filter_height; ++filter_y) {
            const int in_y = in_y_origin + dilation_height_factor * filter_y;
            for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
              const int in_x = in_x_origin + dilation_width_factor * filter_x;

              // Zero padding by omitting the areas outside the image.
              const bool is_point_inside_image =
                  (in_x >= 0) && (in_x < input_width) && (in_y >= 0) && (in_y < input_height);

              if (!is_point_inside_image) {
                continue;
              }

              // DEFAULT IMPLEMENTATION
              for (int in_channel = 0; in_channel < filter_input_depth; ++in_channel) {
                int32_t input_val = input_data[Offset(input_shape, batch, in_y, in_x,
                                                      in_channel + group * filter_input_depth)];
                int32_t filter_val =
                    filter_data[Offset(filter_shape, out_channel, filter_y, filter_x, in_channel)];

                acc += filter_val * (input_val + input_offset);
              }
            }
          }
          if (bias_data) {
            acc += bias_data[out_channel];
          }
          acc = MultiplyByQuantizedMultiplier(acc, output_multiplier[out_channel],
                                              output_shift[out_channel]);
          acc += output_offset;
          acc = std::max(acc, output_activation_min);
          acc = std::min(acc, output_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, out_channel)] =
              static_cast<int8_t>(acc);
        }
      }
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

inline void ConvPerChannelVeryOriginal(const ConvParams& params,
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
  const int32_t input_offset       = params.input_offset;  // r = s(q - Z)
  const int stride_width           = params.stride_width;
  const int stride_height          = params.stride_height;
  const int dilation_width_factor  = params.dilation_width_factor;
  const int dilation_height_factor = params.dilation_height_factor;
  const int pad_width              = params.padding_values.width;
  const int pad_height             = params.padding_values.height;
  const int32_t output_offset      = params.output_offset;

  // Set min and max value of the output.
  const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = params.quantized_activation_max;

  // Consistency check.
  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches      = MatchingDim(input_shape, 0, output_shape, 0);
  const int input_depth  = input_shape.Dims(3);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int input_height       = input_shape.Dims(1);
  const int input_width        = input_shape.Dims(2);
  const int filter_height      = filter_shape.Dims(1);
  const int filter_width       = filter_shape.Dims(2);
  const int filter_input_depth = filter_shape.Dims(3);
  const int groups             = input_depth / filter_input_depth;
  TFLITE_DCHECK_EQ(input_depth % filter_input_depth, 0);
  const int filters_per_group = output_depth / groups;
  const int output_height     = output_shape.Dims(1);
  const int output_width      = output_shape.Dims(2);
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      const int in_y_origin = (out_y * stride_height) - pad_height;
      for (int out_x = 0; out_x < output_width; ++out_x) {
        const int in_x_origin = (out_x * stride_width) - pad_width;
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          auto group  = out_channel / filters_per_group;
          int32_t acc = 0;
          for (int filter_y = 0; filter_y < filter_height; ++filter_y) {
            const int in_y = in_y_origin + dilation_height_factor * filter_y;
            for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
              const int in_x = in_x_origin + dilation_width_factor * filter_x;

              // Zero padding by omitting the areas outside the image.
              const bool is_point_inside_image =
                  (in_x >= 0) && (in_x < input_width) && (in_y >= 0) && (in_y < input_height);

              if (!is_point_inside_image) {
                continue;
              }

              for (int in_channel = 0; in_channel < filter_input_depth; ++in_channel) {
                int32_t input_val = input_data[Offset(input_shape, batch, in_y, in_x,
                                                      in_channel + group * filter_input_depth)];
                int32_t filter_val =
                    filter_data[Offset(filter_shape, out_channel, filter_y, filter_x, in_channel)];
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
                // TODO(b/174275578): Add a check to make sure the
                // accumulator depth is smaller than 2^16.
                acc += filter_val * (input_val + input_offset);
              }
            }
          }

          if (bias_data) {
            acc += bias_data[out_channel];
          }
          acc = MultiplyByQuantizedMultiplier(acc, output_multiplier[out_channel],
                                              output_shift[out_channel]);
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

inline void ConvPerChannelWithPackedInt4Weights(const ConvParams& params,
                                                const int32_t* output_multiplier,
                                                const int32_t* output_shift,
                                                const RuntimeShape& input_shape,
                                                const int8_t* input_data,
                                                const RuntimeShape& filter_shape,
                                                const int8_t* filter_input,
                                                int8_t* unpacked_filter_data,
                                                const RuntimeShape& bias_shape,
                                                const int32_t* bias_data,
                                                const RuntimeShape& output_shape,
                                                int8_t* output_data) {
  TFLITE_DCHECK(unpacked_filter_data != nullptr);
  tflite::tensor_utils::UnpackDenseInt4IntoInt8(filter_input, filter_shape.FlatSize(),
                                                unpacked_filter_data);
  ConvPerChannel(params, output_multiplier, output_shift, input_shape, input_data, filter_shape,
                 unpacked_filter_data, bias_shape, bias_data, output_shape, output_data);
}

// Fixed-point per-channel-quantization convolution reference kernel.
// 16-bit data and 8-bit filter
template <typename AccumScalar>
inline void ConvPerChannel(const ConvParams& params,
                           const int32_t* output_multiplier,
                           const int32_t* output_shift,
                           const RuntimeShape& input_shape,
                           const int16_t* input_data,
                           const RuntimeShape& filter_shape,
                           const int8_t* filter_data,
                           const RuntimeShape& bias_shape,
                           const AccumScalar* bias_data,
                           const RuntimeShape& output_shape,
                           int16_t* output_data) {
  // Get parameters.
  const int stride_width           = params.stride_width;
  const int stride_height          = params.stride_height;
  const int dilation_width_factor  = params.dilation_width_factor;
  const int dilation_height_factor = params.dilation_height_factor;
  const int pad_width              = params.padding_values.width;
  const int pad_height             = params.padding_values.height;

  // Set min and max value of the output.
  const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = params.quantized_activation_max;

  // Consistency check.
  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches      = MatchingDim(input_shape, 0, output_shape, 0);
  const int input_depth  = input_shape.Dims(3);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  if (bias_data) {
    TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);
  }

  // Check dimensions of the tensors.
  const int input_height       = input_shape.Dims(1);
  const int input_width        = input_shape.Dims(2);
  const int filter_height      = filter_shape.Dims(1);
  const int filter_width       = filter_shape.Dims(2);
  const int filter_input_depth = filter_shape.Dims(3);
  const int groups             = input_depth / filter_input_depth;
  TFLITE_DCHECK_EQ(input_depth % filter_input_depth, 0);
  const int filters_per_group = output_depth / groups;
  const int output_height     = output_shape.Dims(1);
  const int output_width      = output_shape.Dims(2);
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      const int in_y_origin = (out_y * stride_height) - pad_height;
      for (int out_x = 0; out_x < output_width; ++out_x) {
        const int in_x_origin = (out_x * stride_width) - pad_width;
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          auto group      = out_channel / filters_per_group;
          AccumScalar acc = 0;
          for (int filter_y = 0; filter_y < filter_height; ++filter_y) {
            const int in_y = in_y_origin + dilation_height_factor * filter_y;
            for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
              const int in_x = in_x_origin + dilation_width_factor * filter_x;

              // Zero padding by omitting the areas outside the image.
              const bool is_point_inside_image =
                  (in_x >= 0) && (in_x < input_width) && (in_y >= 0) && (in_y < input_height);

              if (!is_point_inside_image) {
                continue;
              }

              for (int in_channel = 0; in_channel < filter_input_depth; ++in_channel) {
                int32_t input_val = input_data[Offset(input_shape, batch, in_y, in_x,
                                                      in_channel + group * filter_input_depth)];
                int32_t filter_val =
                    filter_data[Offset(filter_shape, out_channel, filter_y, filter_x, in_channel)];
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
          int32_t scaled_acc = MultiplyByQuantizedMultiplier(acc, output_multiplier[out_channel],
                                                             output_shift[out_channel]);
          scaled_acc         = std::max(scaled_acc, output_activation_min);
          scaled_acc         = std::min(scaled_acc, output_activation_max);
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
