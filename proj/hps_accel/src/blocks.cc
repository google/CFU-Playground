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

#include "blocks.h"
#include "hps_cfu.h"
#include <cstdio>

namespace hps_accel {

namespace {

constexpr size_t BYTES_PER_WORD = 4;

inline uint32_t pack32(int8_t a, int8_t b, int8_t c, int8_t d) {
  return static_cast<uint32_t>(static_cast<uint8_t>(a)) |
         (static_cast<uint32_t>(static_cast<uint8_t>(b)) << 8) |
         (static_cast<uint32_t>(static_cast<uint8_t>(c)) << 16) |
         (static_cast<uint32_t>(static_cast<uint8_t>(d)) << 24);
}

// Data storage for the filter
uint32_t filter_storage[MAX_FILTER_WORDS];

// Current index from which to fetch next Vector16 for filter
size_t filter_index;

// Words in filter storage. Guaranteed to be divisible by 4
size_t filter_words;

// Data storage for input
uint32_t input_storage[MAX_INPUT_WORDS];

// Current index from which to fetch next Vector16 for input
size_t input_index;

// Words in input_storage. Guaranteed to be divisible by 4
size_t input_words;

// Load input when in_channels = 1
void LoadInput1(size_t width, const int8_t* values) {
  input_words = 4;
  uint32_t* dest = input_storage;

  // For each of four consecutive rows, take data from four consecutive pixels
  for (size_t row_index = 0; row_index < 4; row_index++) {
    const int8_t* source = values + (row_index * width);
    *dest++ = pack32(source[0], source[1], source[2], source[3]);
  }
  input_index = 0;
}

// Load input when in_channels is divisible by 4
void LoadInputN(size_t width, size_t in_channels, const int8_t* values) {
  const size_t pixels_per_input_row = 4;
  const size_t words_per_input_row =
      pixels_per_input_row * in_channels / BYTES_PER_WORD;
  const size_t bytes_per_width = width * in_channels;
  input_words = FILTER_WIDTH * FILTER_HEIGHT * in_channels / BYTES_PER_WORD;
  uint32_t* dest = input_storage;

  // For each of four consecutive rows, take data from four consecutive pixels
  for (size_t row_index = 0; row_index < 4; row_index++) {
    const uint32_t* source = reinterpret_cast<const uint32_t*>(
        values + (row_index * bytes_per_width));
    for (size_t i = 0; i < words_per_input_row; i++) {
      *dest++ = *source++;
    }
  }
  input_index = 0;
}


};  // anonymous namespace

Vector16 Vector16::build(int8_t a, int8_t b, int8_t c, int8_t d, int8_t e,
                         int8_t f, int8_t g, int8_t h, int8_t i, int8_t j,
                         int8_t k, int8_t l, int8_t m, int8_t n, int8_t o,
                         int8_t p) {
  return Vector16{{pack32(a, b, c, d), pack32(e, f, g, h), pack32(i, j, k, l),
                   pack32(m, n, o, p)}};
}

Vector16 Vector16::zeroes() { return Vector16{{0, 0, 0, 0}}; }

// Performs a 16 x 16 vector multiplication
int32_t multiply_accumulate(Vector16 input, Vector16 filter,
                            int32_t input_offset) {
  cfu_set(REG_INPUT_OFFSET, input_offset);
  cfu_set(REG_INPUT_0, input.values[0]);
  cfu_set(REG_INPUT_1, input.values[1]);
  cfu_set(REG_INPUT_2, input.values[2]);
  cfu_set(REG_INPUT_3, input.values[3]);
  cfu_set(REG_FILTER_0, filter.values[0]);
  cfu_set(REG_FILTER_1, filter.values[1]);
  cfu_set(REG_FILTER_2, filter.values[2]);
  cfu_set(REG_FILTER_3, filter.values[3]);
  return cfu_get(REG_MACC_OUT);
}

void LoadFilter(size_t in_channels, size_t out_channels, const int8_t* values) {
  const uint32_t* values_as_words = reinterpret_cast<const uint32_t*>(values);
  filter_words = FILTER_WIDTH * FILTER_HEIGHT / 4 * in_channels * out_channels;
  uint32_t* dest = filter_storage;
  uint32_t* end = filter_storage + filter_words;
  while (dest != end) {
    *dest++ = *values_as_words++;
  }
  filter_index = 0;
}

Vector16 GetFilter() {
  Vector16 result{
      {filter_storage[filter_index + 0], filter_storage[filter_index + 1],
       filter_storage[filter_index + 2], filter_storage[filter_index + 3]}};
  filter_index += 4;
  if (filter_index >= filter_words) {
    filter_index = 0;
  }
  return result;
}

void LoadInput(size_t width, size_t in_channels, const int8_t* values) {
    if (in_channels == 1) {
        LoadInput1(width, values);
    } else if ((in_channels & 0x3) == 0) {
        LoadInputN(width, in_channels, values);
    } else {
        printf("Failed to load\n");
    }
}

Vector16 GetInput() {
  Vector16 result{
      {input_storage[input_index + 0], input_storage[input_index + 1],
       input_storage[input_index + 2], input_storage[input_index + 3]}};
  input_index += 4;
  if (input_index >= input_words) {
    input_index = 0;
  }
  return result;
}

};  // namespace hps_accel