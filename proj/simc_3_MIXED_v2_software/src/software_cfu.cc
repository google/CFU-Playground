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

#include "software_cfu.h"
#include <stdint.h>
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>

//
// In this function, place C code to emulate your CFU. You can switch between
// hardware and emulated CFU by setting the CFU_SOFTWARE_DEFINED DEFINE in
// the Makefile.

#define MAX_INPUT_SIZE 1024
#define PADDING 4
#define MAX_PADDED_INPUT_SIZE MAX_INPUT_SIZE + 2 * PADDING
#define MAX_INPUT_CHANNELS 128
#define CONVOLUTE_AT_ONCE 8
#define KERNEL_LENGTH 8

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

uint32_t software_cfu_v6(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  if (funct3 != 0) {
    return 0;
  }

  // Buffers
  static int8_t input_buffer[MAX_INPUT_SIZE * MAX_INPUT_CHANNELS];
  static int8_t kernel_weights_buffer[KERNEL_LENGTH * MAX_INPUT_CHANNELS];

  static int32_t input_offset   = 0;
  static int input_output_width = 0;
  static int input_depth        = 0;

  static int32_t in_x_origin = 0;
  static int32_t acc         = 0;

  // Other variables
  uint32_t address = rs1;
  uint32_t value   = rs2;

  // State machine
  switch (funct7) {
    case 0:  // Zero out buffers
      for (uint32_t in_idx = 0; in_idx < MAX_INPUT_SIZE * MAX_INPUT_CHANNELS; ++in_idx) {
        input_buffer[in_idx] = 0;
      }

      for (uint32_t kernel_idx = 0; kernel_idx < KERNEL_LENGTH * MAX_INPUT_CHANNELS; ++kernel_idx) {
        kernel_weights_buffer[kernel_idx] = 0;
      }

      return 0;

    case 10:  // Write to input buffer
      input_buffer[address] = (int8_t)value;
      return 0;
    case 11:  // Write to kernel weights buffer
      kernel_weights_buffer[address] = (int8_t)value;
      return 0;
    case 13:  // Read input buffer
      return input_buffer[address];
    case 14:  // Read kernel weights buffer
      return kernel_weights_buffer[address];
    case 20:  // Write input offset
      input_offset = (int32_t)value;
      return input_offset;
    case 25:  // Write input_output_width
      input_output_width = (int)value;
      return input_output_width;
    case 26:  // Write input_depth
      input_depth = (int)value;
      return input_depth;

    case 41:  // Start computation
      acc = 0;
      for (int filter_x = 0; filter_x < 8; ++filter_x) {
        int32_t in_x = in_x_origin + filter_x;
        for (int in_channel = 0; in_channel < MAX_INPUT_CHANNELS; ++in_channel) {
          if ((in_x >= 0) && (in_x < input_output_width) && (in_channel < input_depth)) {
            acc += kernel_weights_buffer[filter_x * input_depth + in_channel] *
                   (input_buffer[in_x * input_depth + in_channel] + input_offset);
          }
        }
      }
      return 0;
    case 42:
      in_x_origin = value;
      return 0;
    case 43:
      return acc;
    default:
      return 0;
  }
}

// Doesn't do quantization
uint32_t software_cfu_v4(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  if (funct3 != 0) {
    return 0;
  }

  // Buffers
  static int8_t input_buffer[MAX_INPUT_SIZE * MAX_INPUT_CHANNELS];
  static int8_t kernel_weights_buffer[KERNEL_LENGTH * MAX_INPUT_CHANNELS];
  static int32_t output_buffer[MAX_INPUT_SIZE];

  static int32_t bias;
  static int32_t output_multiplier;
  (void)output_multiplier;
  static int32_t output_shift;
  (void)output_shift;

  // Static variables
  // static int8_t bias          = 0;
  static int32_t input_offset = 0;

  static int32_t output_offset         = 0;
  static int32_t output_activation_min = 0;
  static int32_t output_activation_max = 0;

  static int output_depth       = 0;
  static int input_output_width = 0;
  static int input_depth        = 0;

  // Other variables
  uint32_t address = rs1;
  uint32_t value   = rs2;

  // State machine
  switch (funct7) {
    case 0:  // Zero out buffers
      for (uint32_t out_idx = 0; out_idx < MAX_INPUT_SIZE; ++out_idx) {
        output_buffer[out_idx] = 0;
      }

      for (uint32_t in_idx = 0; in_idx < MAX_INPUT_SIZE * MAX_INPUT_CHANNELS; ++in_idx) {
        input_buffer[in_idx] = 0;
      }

      for (uint32_t kernel_idx = 0; kernel_idx < KERNEL_LENGTH * MAX_INPUT_CHANNELS; ++kernel_idx) {
        kernel_weights_buffer[kernel_idx] = 0;
      }

      bias              = 0;
      output_multiplier = 0;
      output_shift      = 0;
      return 0;

    case 10:  // Write to input buffer
      input_buffer[address] = (int8_t)value;
      return 0;
    case 11:  // Write to kernel weights buffer
      kernel_weights_buffer[address] = (int8_t)value;
      return 0;
    case 12:  // Read output buffer
      return output_buffer[address];
    case 13:  // Read input buffer
      return input_buffer[address];
    case 14:  // Read kernel weights buffer
      return kernel_weights_buffer[address];
    case 15:  // Zero out output buffer
      for (uint32_t out_idx = 0; out_idx < MAX_INPUT_SIZE; ++out_idx) {
        output_buffer[out_idx] = 0;
      }
      return 0;
    case 20:  // Write input offset
      input_offset = (int32_t)value;
      return input_offset;
    case 21:  // Write output_offset
      output_offset = (int32_t)value;
      return output_offset;
    case 22:  // Write output_activation_min
      output_activation_min = (int32_t)value;
      return output_activation_min;
    case 23:  // Write output_activation_max
      output_activation_max = (int32_t)value;
      return output_activation_max;
    case 24:  // Write output_depth
      output_depth = (int)value;
      return output_depth;
    case 25:  // Write input_output_width
      input_output_width = (int)value;
      return input_output_width;
    case 26:  // Write input_depth
      input_depth = (int)value;
      return input_depth;
    case 27:  // Write bias_buffer
      bias = (int32_t)value;
      return 0;
    case 28:  // Write output_multiplier_buffer
      output_multiplier = (int32_t)value;
      return 0;
    case 29:  // Write output_shift_buffer
      output_shift = (int32_t)value;
      return 0;

    case 40:  // Start computation
      for (int out_x = 0; out_x < MAX_INPUT_SIZE; ++out_x) {
        const int in_x_origin = out_x - (PADDING - 1);
        // int32_t acc           = 0;
        for (int filter_x = 0; filter_x < 8; ++filter_x) {
          const int in_x = in_x_origin + filter_x;
          for (int in_channel = 0; in_channel < MAX_INPUT_CHANNELS; ++in_channel) {
            if ((in_x >= 0) && (in_x < input_output_width) && (in_channel < input_depth)) {
              output_buffer[out_x] +=
                  kernel_weights_buffer[filter_x * input_depth + in_channel] *
                  (input_buffer[in_x * input_depth + in_channel] + input_offset);
            }
          }
        }

        output_buffer[out_x] += bias;
        // output_buffer[out_x] = static_cast<int32_t>(acc);
      }
      return 0;
    default:
      return 0;
  }
}

uint32_t software_cfu_v3(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  if (funct3 != 0) {
    return 0;
  }

  // Buffers
  static int8_t input_buffer[MAX_INPUT_SIZE * MAX_INPUT_CHANNELS];
  static int8_t kernel_weights_buffer[KERNEL_LENGTH * MAX_INPUT_CHANNELS];
  static int8_t output_buffer[MAX_INPUT_SIZE];

  static int32_t bias;
  static int32_t output_multiplier;
  static int32_t output_shift;

  // Static variables
  // static int8_t bias          = 0;
  static int32_t input_offset = 0;

  static int32_t output_offset         = 0;
  static int32_t output_activation_min = 0;
  static int32_t output_activation_max = 0;

  static int output_depth       = 0;
  static int input_output_width = 0;
  static int input_depth        = 0;

  // Other variables
  uint32_t address = rs1;
  uint32_t value   = rs2;

  // State machine
  switch (funct7) {
    case 00:  // Zero out buffers
      for (uint32_t out_idx = 0; out_idx < MAX_INPUT_SIZE; ++out_idx) {
        output_buffer[out_idx] = 0;
      }

      for (uint32_t in_idx = 0; in_idx < MAX_INPUT_SIZE * MAX_INPUT_CHANNELS; ++in_idx) {
        input_buffer[in_idx] = 0;
      }

      for (uint32_t kernel_idx = 0; kernel_idx < KERNEL_LENGTH * MAX_INPUT_CHANNELS; ++kernel_idx) {
        kernel_weights_buffer[kernel_idx] = 0;
      }

      bias              = 0;
      output_multiplier = 0;
      output_shift      = 0;
      return 0;

    case 10:  // Write to input buffer
      input_buffer[address] = (int8_t)value;
      return 0;
    case 20:  // Write to kernel weights buffer
      kernel_weights_buffer[address] = (int8_t)value;
      return 0;
    case 30:  // Read output buffer
      return output_buffer[address];
    case 40:  // Read input buffer
      return input_buffer[address];
    case 50:  // Read kernel weights buffer
      return kernel_weights_buffer[address];
    // case 60:  // Write bias
    //   bias = (int8_t)rs1;
    //   return bias;
    case 70:  // Write input offset
      input_offset = (int32_t)rs1;
      return input_offset;
    case 80:  // Write output_offset
      output_offset = (int32_t)rs1;
      return output_offset;
    case 90:  // Write output_activation_min
      output_activation_min = (int32_t)rs1;
      return output_activation_min;
    case 100:  // Write output_activation_max
      output_activation_max = (int32_t)rs1;
      return output_activation_max;
    case 110:  // Write output_depth
      output_depth = (int)rs1;
      return output_depth;
    case 120:  // Write input_output_width
      input_output_width = (int)rs1;
      return input_output_width;
    case 130:  // Write input_depth
      input_depth = (int)rs1;
      return input_depth;
    case 140:  // Write bias_buffer
      bias = (int32_t)rs1;
      return 0;
    case 150:  // Write output_multiplier_buffer
      output_multiplier = (int32_t)rs1;
      return 0;
    case 160:  // Write output_shift_buffer
      output_shift = (int32_t)rs1;
      return 0;

    case 170:  // Start computation
      for (int out_x = 0; out_x < input_output_width; ++out_x) {
        const int in_x_origin = out_x - (PADDING - 1);
        int32_t acc           = 0;
        for (int filter_x = 0; filter_x < 8; ++filter_x) {
          const int in_x = in_x_origin + filter_x;

          // Zero padding by omitting the areas outside the image.
          const bool is_point_inside_image = (in_x >= 0) && (in_x < input_output_width);

          for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
            int32_t input_val  = input_buffer[in_x * input_depth + in_channel];
            int32_t filter_val = kernel_weights_buffer[filter_x * input_depth + in_channel];

            acc += is_point_inside_image ? filter_val * (input_val + input_offset) : 0;
          }
        }

        acc += bias;
        acc = multiply_by_quant_mult(acc, output_multiplier, output_shift);
        acc += output_offset;
        acc                  = std::max(acc, output_activation_min);
        acc                  = std::min(acc, output_activation_max);
        output_buffer[out_x] = static_cast<int8_t>(acc);
      }
      return 0;
    default:
      return 0;
  }
}

#define MAX_OUTPUT_CHANNELS 192
uint32_t software_cfu_v2(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  if (funct3 != 0) {
    return 0;
  }

  // Buffers
  static int8_t input_buffer[MAX_INPUT_SIZE * MAX_INPUT_CHANNELS];
  static int8_t kernel_weights_buffer[KERNEL_LENGTH * MAX_INPUT_CHANNELS * MAX_OUTPUT_CHANNELS];
  static int8_t output_buffer[MAX_INPUT_SIZE * MAX_OUTPUT_CHANNELS];
  static int32_t bias_buffer[MAX_OUTPUT_CHANNELS];
  static int32_t output_multiplier_buffer[MAX_OUTPUT_CHANNELS];
  static int32_t output_shift_buffer[MAX_OUTPUT_CHANNELS];

  // Static variables
  // static int8_t bias          = 0;
  static int32_t input_offset = 0;

  static int32_t output_offset         = 0;
  static int32_t output_activation_min = 0;
  static int32_t output_activation_max = 0;

  static int output_depth       = 0;
  static int input_output_width = 0;
  static int input_depth        = 0;

  // Other variables
  uint32_t address = rs1;
  uint32_t value   = rs2;

  // State machine
  switch (funct7) {
    case 00:  // Zero out buffers
      for (uint32_t out_idx = 0; out_idx < MAX_INPUT_SIZE * MAX_OUTPUT_CHANNELS; ++out_idx) {
        output_buffer[out_idx] = 0;
      }

      for (uint32_t in_idx = 0; in_idx < MAX_INPUT_SIZE * MAX_INPUT_CHANNELS; ++in_idx) {
        input_buffer[in_idx] = 0;
      }

      for (uint32_t kernel_idx = 0;
           kernel_idx < KERNEL_LENGTH * MAX_INPUT_CHANNELS * MAX_OUTPUT_CHANNELS; ++kernel_idx) {
        kernel_weights_buffer[kernel_idx] = 0;
      }

      for (uint32_t output_channel = 0; output_channel < MAX_OUTPUT_CHANNELS; ++output_channel) {
        bias_buffer[output_activation_max]              = 0;
        output_multiplier_buffer[output_activation_max] = 0;
        output_shift_buffer[output_activation_max]      = 0;
      }
      return 0;

    case 10:  // Write to input buffer
      input_buffer[address] = (int8_t)value;
      return 0;
    case 20:  // Write to kernel weights buffer
      kernel_weights_buffer[address] = (int8_t)value;
      return 0;
    case 30:  // Read output buffer
      return output_buffer[address];
    case 40:  // Read input buffer
      return input_buffer[address];
    case 50:  // Read kernel weights buffer
      return kernel_weights_buffer[address];
    // case 60:  // Write bias
    //   bias = (int8_t)rs1;
    //   return bias;
    case 70:  // Write input offset
      input_offset = (int32_t)rs1;
      return input_offset;
    case 80:  // Write output_offset
      output_offset = (int32_t)rs1;
      return output_offset;
    case 90:  // Write output_activation_min
      output_activation_min = (int32_t)rs1;
      return output_activation_min;
    case 100:  // Write output_activation_max
      output_activation_max = (int32_t)rs1;
      return output_activation_max;
    case 110:  // Write output_depth
      output_depth = (int)rs1;
      return output_depth;
    case 120:  // Write input_output_width
      input_output_width = (int)rs1;
      return input_output_width;
    case 130:  // Write input_depth
      input_depth = (int)rs1;
      return input_depth;
    case 140:  // Write bias_buffer
      bias_buffer[address] = (int32_t)value;
      return 0;
    case 150:  // Write output_multiplier_buffer
      output_multiplier_buffer[address] = (int32_t)value;
      return 0;
    case 160:  // Write output_shift_buffer
      output_shift_buffer[address] = (int32_t)value;
      return 0;

    case 170:  // Start computation
      for (int out_x = 0; out_x < input_output_width; ++out_x) {
        const int in_x_origin = out_x - (PADDING - 1);
        for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
          int32_t acc = 0;
          for (int filter_x = 0; filter_x < 8; ++filter_x) {
            const int in_x = in_x_origin + filter_x;

            // Zero padding by omitting the areas outside the image.
            const bool is_point_inside_image = (in_x >= 0) && (in_x < input_output_width);
            if (!is_point_inside_image) {
              continue;
            }

            for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
              int32_t input_val  = input_buffer[in_x * input_depth + in_channel];
              int32_t filter_val = kernel_weights_buffer[out_channel * (8 * input_depth) +
                                                         filter_x * input_depth + in_channel];

              acc += filter_val * (input_val + input_offset);
            }
          }

          acc += bias_buffer[out_channel];
          acc = multiply_by_quant_mult(acc, (int32_t)output_multiplier_buffer[out_channel],
                                       (int32_t)output_shift_buffer[out_channel]);
          acc += output_offset;
          acc                                               = std::max(acc, output_activation_min);
          acc                                               = std::min(acc, output_activation_max);
          output_buffer[out_x * output_depth + out_channel] = static_cast<int8_t>(acc);
        }
      }
      return 0;
    default:
      return 0;
  }
}

uint32_t software_cfu_v1(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  if (funct3 != 0) {
    return 0;
  }

  // Buffers
  static int8_t input_buffer[MAX_PADDED_INPUT_SIZE][MAX_INPUT_CHANNELS];
  static int8_t kernel_weights_buffer[KERNEL_LENGTH][MAX_INPUT_CHANNELS];
  static uint32_t output_buffer[MAX_INPUT_SIZE];

  // Static variables
  static int8_t bias          = 0;
  static int32_t input_offset = 0;

  // Other variables
  uint32_t address     = rs1;
  uint32_t value       = rs2;
  uint32_t address_row = rs1 / MAX_INPUT_CHANNELS;
  uint32_t address_col = rs1 % MAX_INPUT_CHANNELS;

  // State machine
  switch (funct7) {
    case 00:  // Zero out buffers
      for (uint32_t out_idx = 0; out_idx < MAX_INPUT_SIZE; ++out_idx) {
        output_buffer[out_idx] = 0;
      }

      for (uint32_t in_idx = 0; in_idx < MAX_PADDED_INPUT_SIZE; ++in_idx) {
        for (uint32_t channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; ++channel_idx) {
          input_buffer[in_idx][channel_idx] = 0;
        }
      }

      for (uint32_t kernel_idx = 0; kernel_idx < KERNEL_LENGTH; ++kernel_idx) {
        for (uint32_t channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; ++channel_idx) {
          kernel_weights_buffer[kernel_idx][channel_idx] = 0;
        }
      }
      return 0;

    case 10:  // Write to input buffer
      input_buffer[address_row][address_col] = (int8_t)value;
      return 0;
    case 20:  // Write to kernel weights buffer
      kernel_weights_buffer[address_row][address_col] = (int8_t)value;
      return 0;
    case 30:  // Read output buffer
      return output_buffer[address];
    case 40:  // Start computation
      for (uint32_t out_idx = 0; out_idx < MAX_INPUT_SIZE; ++out_idx) {
        for (uint32_t channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; ++channel_idx) {
          // uint32_t before = output_buffer[out_idx];
          output_buffer[out_idx] += input_buffer[(PADDING + out_idx - 3)][channel_idx] *
                                        (kernel_weights_buffer[0][channel_idx] + input_offset) +
                                    input_buffer[(PADDING + out_idx - 2)][channel_idx] *
                                        (kernel_weights_buffer[1][channel_idx] + input_offset) +
                                    input_buffer[(PADDING + out_idx - 1)][channel_idx] *
                                        (kernel_weights_buffer[2][channel_idx] + input_offset) +
                                    input_buffer[(PADDING + out_idx)][channel_idx] *
                                        (kernel_weights_buffer[3][channel_idx] + input_offset) +
                                    input_buffer[(PADDING + out_idx + 1)][channel_idx] *
                                        (kernel_weights_buffer[4][channel_idx] + input_offset) +
                                    input_buffer[(PADDING + out_idx + 2)][channel_idx] *
                                        (kernel_weights_buffer[5][channel_idx] + input_offset) +
                                    input_buffer[(PADDING + out_idx + 3)][channel_idx] *
                                        (kernel_weights_buffer[6][channel_idx] + input_offset) +
                                    input_buffer[(PADDING + out_idx + 4)][channel_idx] *
                                        (kernel_weights_buffer[7][channel_idx] + input_offset);
        }
        output_buffer[out_idx] += bias;
      }
      return 0;
    case 50:  // Read input buffer
      return input_buffer[address_row][address_col];
    case 60:  // Read kernel weights buffer
      return kernel_weights_buffer[address_row][address_col];
    case 70:  // Write bias
      bias = (int8_t)rs1;
      return bias;
    case 80:  // Write input offset
      input_offset = (int32_t)rs1;
      return input_offset;
    default:
      return 0;
  }
}

uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  return software_cfu_v6(funct3, funct7, rs1, rs2);
}