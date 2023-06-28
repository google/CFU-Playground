#pragma once

#include "software_cfu_common.hh"


/*
  Input buffer is now a ring buffer with much smaller size. 
  This optimization is not free, since now more input copy calls are required
*/
uint32_t software_cfu_v7(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  if (funct3 != 0) {
    return 0;
  }

  // Buffers
  // static int8_t input_buffer[MAX_INPUT_SIZE * MAX_INPUT_CHANNELS];
  static int8_t input_buffer[KERNEL_LENGTH * MAX_INPUT_CHANNELS];
  static int8_t kernel_weights_buffer[KERNEL_LENGTH * MAX_INPUT_CHANNELS];

  static int32_t input_offset   = 0;
  static int input_output_width = 0;
  static int input_depth        = 0;

  static int32_t in_x_origin = 0;
  (void)in_x_origin;
  static int32_t start_filter_x = 0;
  static int32_t acc            = 0;

  // Other variables
  uint32_t address = rs1;
  uint32_t value   = rs2;

  // State machine
  switch (funct7) {
    case 0:
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
        for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
          int kernel_addr = filter_x * input_depth + in_channel;
          int input_addr = ((filter_x + start_filter_x) % 8) * input_depth + in_channel;
          acc += kernel_weights_buffer[kernel_addr] * (input_buffer[input_addr] + input_offset);
          // printf("%ld: acc += %d * (%d + %ld)\n", (filter_x + start_filter_x) % 8,
          //        kernel_weights_buffer[kernel_addr], input_buffer[input_addr], input_offset);
        }
      }
      return 0;
    case 42:
      in_x_origin = value;
      return 0;
    case 43:
      return acc;
    case 44:
      start_filter_x = value;
      return 0;
    default:
      return 0;
  }
}
