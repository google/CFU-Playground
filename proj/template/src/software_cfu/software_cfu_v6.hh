#pragma once

#include "software_cfu_common.hh"

/*
    iteration over out_x is moved out of cfu
    This basically removes the whole output buffer
*/
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
