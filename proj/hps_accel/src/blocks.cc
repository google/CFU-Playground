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

namespace hps_accel {

namespace {

inline uint32_t pack32(int8_t a, int8_t b, int8_t c, int8_t d) {
  return static_cast<uint32_t>(static_cast<uint8_t>(a)) |
         (static_cast<uint32_t>(static_cast<uint8_t>(b)) << 8) |
         (static_cast<uint32_t>(static_cast<uint8_t>(c)) << 16) |
         (static_cast<uint32_t>(static_cast<uint8_t>(d)) << 24);
}

int32_t multiply_1(int8_t input, int8_t filter, int32_t input_offset) {
  return (input_offset + input) * filter;
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
  int32_t result = 0;
  // NOTE: obvious optimization is to unroll these loops
  for (size_t n = 0; n < 16; n++) {
    result += multiply_1(input.get(n), filter.get(n), input_offset);
  }
  return result;
}

void LoadFilter(size_t in_channels, size_t out_channels,
                const uint32_t* values) {
  filter_words = FILTER_WIDTH * FILTER_HEIGHT / 4 * in_channels * out_channels;
  uint32_t* dest = filter_storage;
  uint32_t* end = filter_storage + filter_words;
  while (dest != end) {
    *dest++ = *values++;
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

void LoadInput(size_t width, size_t in_channels, const uint32_t* values) {
  // TODO: make this work when in_channels = 1
  const size_t words_per_pixel = in_channels / 4;
  const size_t words_per_vector_row = words_per_pixel * 4;
  const size_t words_per_width = words_per_pixel * width;
  input_words = FILTER_WIDTH * FILTER_HEIGHT * words_per_pixel;
  uint32_t* dest = input_storage;

  // For each of four consecutive rows, take date from four consecutive pixels
  for (size_t row_index = 0; row_index < 4; row_index++) {
    const uint32_t* source = values + (row_index * words_per_width);
    for (size_t i = 0; i < words_per_vector_row; i++) {
      *dest++ = *source++;
    }
  }
  input_index = 0;
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