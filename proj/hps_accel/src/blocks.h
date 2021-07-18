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
// Enocodes 16 signed 8-bit values in a 4x4 matrix
struct Matrix4x4 {
  // values is indexed by y. Each 32 bit value holds 4 values, in little endian
  // order
  uint32_t values[4];

  // Fetches a single 8bit value
  inline int8_t get(size_t y, size_t x) {
    uint32_t row = values[y];
    size_t shift = x * 8;
    uint32_t byte_mask = 0xff << shift;
    uint32_t byte_value = (row & byte_mask) >> shift;
    return static_cast<int8_t>(byte_value);
  }
};

// Performs a 4x4 matrix multiplication
Matrix4x4 multiply(Matrix4x4 input, Matrix4x4 filter, int32_t input_offset);

// Loads 4x4 filter values into global filter storage.
//
// - in_channels and outchannels are the number of input and output channels for
//   this filter. Both must be divisible by 4.
// - filter width & height are assumed to be 4.
//
// The number of 32 bit values loaded is:
//   in_channels * 4*4 * out_channels / 4
//
void LoadFilter(size_t in_channels, size_t out_channels, uint32_t* values);

// Returns the filter to use for the next multiplication
// Iterates through filters for each input channel within output channel and
// restarts from beginning when it reaches the end
Matrix4x4 GetFilter();

// Loads input values into global input storage.
//
// - width is length of row
// - in_channels are the number of input channels. Must be divisible by 4.
// - values is address of first word to load. It is the top left pixel.
void LoadValues(size_t width, size_t in_channels, uint32_t values);

// Returns next matrix of input values to use.
// Iterates through each input channel, then returns to start
Matrix4x4 GetValue();

};  // namespace hps_accel

#endif  // _BLOCKS_H