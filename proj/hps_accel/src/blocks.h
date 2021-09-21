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

// Some useful building blocks for an initial accelerator architecture
#ifndef _BLOCKS_H
#define _BLOCKS_H

#include <cstddef>
#include <cstdint>

#include "hps_cfu.h"

namespace hps_accel {

// All filters are 4x4
constexpr size_t FILTER_WIDTH = 4;
constexpr size_t FILTER_HEIGHT = 4;

// Encodes 16 signed 8-bit values in a 4x32 bit words
struct Vector16 {
  // Each 32 bit value holds four 8 bit signed values, in little endian order.
  uint32_t values[4];

  // Fetches a single 8bit value
  inline int8_t get(size_t n) const {
    uint32_t col = n & 0x3;
    size_t shift = col * 8;
    uint32_t byte_mask = 0xff << shift;
    uint32_t val = values[n >> 2];
    uint32_t byte_value = (val & byte_mask) >> shift;
    return static_cast<int8_t>(byte_value);
  }

  inline bool same_values(Vector16 other) const {
    for (size_t i = 0; i < 16; i++) {
      if (get(i) != other.get(i)) return false;
    }
    return true;
  }

  // Convenience function: builds a new vector from int8_t's
  static Vector16 build(int8_t a, int8_t b, int8_t c, int8_t d, int8_t e,
                        int8_t f, int8_t g, int8_t h, int8_t i, int8_t j,
                        int8_t k, int8_t l, int8_t m, int8_t n, int8_t o,
                        int8_t p);
  static Vector16 zeroes();
};

// Returns the result of the current 4x4 matrix multiply-accumulate operation
inline int32_t multiply_accumulate() { return cfu_get(REG_MACC_OUT); }

// Loads 4x4 filter values into global filter storage.
//
// - in_channels: the number of input channels. Must either be 1 or a number
//   divisible by 4.
// - outchannels: the number of output channels. Must be divisible by 4.
// - filter width & height are assumed to be 4.
//
// The number of 32 bit values loaded is:
//   in_channels * 4*4 * out_channels / 4
//
void LoadFilter(size_t in_channels, size_t out_channels, const int8_t* values);

// Returns the filter to use for the next multiplication
// Iterates through filters for each input channel within x, within y within
// output_channel and restarts from beginning when it reaches the end
Vector16 GetFilter();

// Loads a single input offset value into global storage.
// This offset is applied to every multiply_accumulate() operation.
inline void LoadInputOffset(int32_t value) { cfu_set(REG_INPUT_OFFSET, value); }

// Loads 4x4 pixels of input values into global input storage.
//
// - width is length of row, in pixels
// - in_channels are the number of input channels. Must be divisible by 4.
// - values is address of first word to load. It is the top left pixel.
void LoadInput(size_t width, size_t in_channels, const int8_t* values);

// Returns next matrix of input values to use.
// Iterates through each input channel, then returns to start
Vector16 GetInput();

inline void AdvanceFilterInput() { cfu_set(REG_FILTER_INPUT_NEXT, 0); }

// Sets per-layer output parameters
void SetOutputOffsets(int32_t output_offset, int32_t output_activation_min,
                      int32_t output_activation_max);

// Loads output parameters
void LoadOutputParams(size_t offset, size_t count, const int32_t* bias_data,
                      const int32_t* output_multiplier,
                      const int32_t* output_shift);

// Do the actual post-processing
inline int32_t PostProcess(int32_t acc) {
  return cfu_op2(PP_POST_PROCESS, acc, 0);
}

// Math functions

// Same as tflite::MultiplyByQuantizedMultiplier but assumes:
// shift is in the range -4 to -10 (inclusive)
// multiplier is in the range 0x40000000 to 0x7fffffff

// Main implementation for use in code
inline int32_t MultiplyByQuantizedMultiplier(int32_t x, int32_t multiplier,
                                             int shift) {
  int32_t product = cfu_op2(PP_SRDHM, x, multiplier);
  return cfu_op2(PP_RDBPOT, product, shift);
}

// Same functionality. Uses software CFU implementations of component
// operations.
int32_t MultiplyByQuantizedMultiplier_01(int32_t x, int32_t multiplier,
                                         int shift);

// Same functionality. Reimplements RoundingDivideByPOT
int32_t MultiplyByQuantizedMultiplier_02(int32_t x, int32_t multiplier,
                                         int shift);

// Same functionality. Reimplements SaturatingRoundingDoubleHighMul
int32_t MultiplyByQuantizedMultiplier_03(int32_t x, int32_t multiplier,
                                         int shift);

// Same functionality. Simplifies operations to be more amenable to running on
// FPGA
int32_t MultiplyByQuantizedMultiplier_04(int32_t x, int32_t multiplier,
                                         int shift);

// Same functionality. Uses software CFU implementations of operation
int32_t MultiplyByQuantizedMultiplier_SW(int32_t x, int32_t multiplier,
                                         int shift);

// Same functionality. Uses hardware CFU implementations of component
// operations.
int32_t MultiplyByQuantizedMultiplier_HW(int32_t x, int32_t multiplier,
                                         int shift);

// Reset all
inline void Reset() { cfu_set(REG_RESET, 0); }

};  // namespace hps_accel

#endif  // _BLOCKS_H
