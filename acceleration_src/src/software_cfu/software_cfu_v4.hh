#pragma once

#include "software_cfu_common.hh"



/*
    The same as v3, but doesn't do quantization
*/
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