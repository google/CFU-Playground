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
#include <cstdint>
#include <cstdio>
#include "software_cfu_common.hh"
#include "software_cfu_v2.hh"
#include "software_cfu_v3.hh"
#include "software_cfu_v4.hh"
#include "software_cfu_v6.hh"
#include "software_cfu_v7.hh"

//
// In this function, place C code to emulate your CFU. You can switch between
// hardware and emulated CFU by setting the CFU_SOFTWARE_DEFINED DEFINE in
// the Makefile.

uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  return software_cfu_v7(funct3, funct7, rs1, rs2);
}

// Doesn' work
// uint32_t software_cfu_v1(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
//   if (funct3 != 0) {
//     return 0;
//   }

//   // Buffers
//   static int8_t input_buffer[MAX_PADDED_INPUT_SIZE][MAX_INPUT_CHANNELS];
//   static int8_t kernel_weights_buffer[KERNEL_LENGTH][MAX_INPUT_CHANNELS];
//   static uint32_t output_buffer[MAX_INPUT_SIZE];

//   // Static variables
//   static int8_t bias          = 0;
//   static int32_t input_offset = 0;

//   // Other variables
//   uint32_t address     = rs1;
//   uint32_t value       = rs2;
//   uint32_t address_row = rs1 / MAX_INPUT_CHANNELS;
//   uint32_t address_col = rs1 % MAX_INPUT_CHANNELS;

//   // State machine
//   switch (funct7) {
//     case 00:  // Zero out buffers
//       for (uint32_t out_idx = 0; out_idx < MAX_INPUT_SIZE; ++out_idx) {
//         output_buffer[out_idx] = 0;
//       }

//       for (uint32_t in_idx = 0; in_idx < MAX_PADDED_INPUT_SIZE; ++in_idx) {
//         for (uint32_t channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; ++channel_idx) {
//           input_buffer[in_idx][channel_idx] = 0;
//         }
//       }

//       for (uint32_t kernel_idx = 0; kernel_idx < KERNEL_LENGTH; ++kernel_idx) {
//         for (uint32_t channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; ++channel_idx) {
//           kernel_weights_buffer[kernel_idx][channel_idx] = 0;
//         }
//       }
//       return 0;

//     case 10:  // Write to input buffer
//       input_buffer[address_row][address_col] = (int8_t)value;
//       return 0;
//     case 20:  // Write to kernel weights buffer
//       kernel_weights_buffer[address_row][address_col] = (int8_t)value;
//       return 0;
//     case 30:  // Read output buffer
//       return output_buffer[address];
//     case 40:  // Start computation
//       for (uint32_t out_idx = 0; out_idx < MAX_INPUT_SIZE; ++out_idx) {
//         for (uint32_t channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; ++channel_idx) {
//           // uint32_t before = output_buffer[out_idx];
//           output_buffer[out_idx] += input_buffer[(PADDING + out_idx - 3)][channel_idx] *
//                                         (kernel_weights_buffer[0][channel_idx] + input_offset) +
//                                     input_buffer[(PADDING + out_idx - 2)][channel_idx] *
//                                         (kernel_weights_buffer[1][channel_idx] + input_offset) +
//                                     input_buffer[(PADDING + out_idx - 1)][channel_idx] *
//                                         (kernel_weights_buffer[2][channel_idx] + input_offset) +
//                                     input_buffer[(PADDING + out_idx)][channel_idx] *
//                                         (kernel_weights_buffer[3][channel_idx] + input_offset) +
//                                     input_buffer[(PADDING + out_idx + 1)][channel_idx] *
//                                         (kernel_weights_buffer[4][channel_idx] + input_offset) +
//                                     input_buffer[(PADDING + out_idx + 2)][channel_idx] *
//                                         (kernel_weights_buffer[5][channel_idx] + input_offset) +
//                                     input_buffer[(PADDING + out_idx + 3)][channel_idx] *
//                                         (kernel_weights_buffer[6][channel_idx] + input_offset) +
//                                     input_buffer[(PADDING + out_idx + 4)][channel_idx] *
//                                         (kernel_weights_buffer[7][channel_idx] + input_offset);
//         }
//         output_buffer[out_idx] += bias;
//       }
//       return 0;
//     case 50:  // Read input buffer
//       return input_buffer[address_row][address_col];
//     case 60:  // Read kernel weights buffer
//       return kernel_weights_buffer[address_row][address_col];
//     case 70:  // Write bias
//       bias = (int8_t)rs1;
//       return bias;
//     case 80:  // Write input offset
//       input_offset = (int32_t)rs1;
//       return input_offset;
//     default:
//       return 0;
//   }
// }