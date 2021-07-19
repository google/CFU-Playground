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

};  // anonymous namespace

namespace hps_accel {

Matrix4x4 Matrix4x4::build(int8_t a, int8_t b, int8_t c, int8_t d, int8_t e,
                           int8_t f, int8_t g, int8_t h, int8_t i, int8_t j,
                           int8_t k, int8_t l, int8_t m, int8_t n, int8_t o,
                           int8_t p) {
  return Matrix4x4{{pack32(a, b, c, d), pack32(e, f, g, h), pack32(i, j, k, l),
                    pack32(m, n, o, p)}};
}

Matrix4x4 Matrix4x4::zeroes() { return Matrix4x4{{0, 0, 0, 0}}; }

// Performs a 4x4 matrix multiplication
int32_t multiply_accumulate(Matrix4x4 input, Matrix4x4 filter,
                            int32_t input_offset) {
  int32_t result = 0;
  // NOTE: obvious optimization is to unroll these loops
  for (size_t y = 0; y < 4; y++) {
    for (size_t x = 0; x < 4; x++) {
      result += multiply_1(input.get(y, x), filter.get(y, x), input_offset);
    }
  }
  return result;
}

};  // namespace hps_accel