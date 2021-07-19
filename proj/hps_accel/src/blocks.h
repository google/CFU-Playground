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

namespace hps_accel {

// All filters are 4x4
constexpr size_t FILTER_WIDTH = 4;
constexpr size_t FILTER_HEIGHT = 4;

// Maximum number of words in filter
// TODO: this has to come down to ~ 2k and then change code to make batches to
// match
constexpr size_t MAX_FILTER_WORDS = 16384;

// Maximum number of words in input
constexpr size_t MAX_INPUT_WORDS = 256;

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

  static Vector16 build(int8_t a, int8_t b, int8_t c, int8_t d, int8_t e,
                        int8_t f, int8_t g, int8_t h, int8_t i, int8_t j,
                        int8_t k, int8_t l, int8_t m, int8_t n, int8_t o,
                        int8_t p);
  static Vector16 zeroes();
};

// Performs a 4x4 matrix multiply-accumulate operation
int32_t multiply_accumulate(Vector16 input, Vector16 filter,
                            int32_t input_offset);

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
void LoadFilter(size_t in_channels, size_t out_channels,
                const uint32_t* values);

// Returns the filter to use for the next multiplication
// Iterates through filters for each input channel within x, within y within
// output_channel and restarts from beginning when it reaches the end
Vector16 GetFilter();

// Loads 4x4 pixels of input values into global input storage.
//
// - width is length of row, in pixels
// - in_channels are the number of input channels. Must be divisible by 4.
// - values is address of first word to load. It is the top left pixel.
void LoadInput(size_t width, size_t in_channels, const uint32_t* values);

// Returns next matrix of input values to use.
// Iterates through each input channel, then returns to start
Vector16 GetInput();

};  // namespace hps_accel

#endif  // _BLOCKS_H