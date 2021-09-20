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

#include <cstdio>

#include "hps_cfu.h"
#include "tensorflow/lite/kernels/internal/common.h"

namespace hps_accel {

namespace {

constexpr size_t BYTES_PER_WORD = 4;

inline uint32_t pack32(int8_t a, int8_t b, int8_t c, int8_t d) {
  return static_cast<uint32_t>(static_cast<uint8_t>(a)) |
         (static_cast<uint32_t>(static_cast<uint8_t>(b)) << 8) |
         (static_cast<uint32_t>(static_cast<uint8_t>(c)) << 16) |
         (static_cast<uint32_t>(static_cast<uint8_t>(d)) << 24);
}

// Load input when in_channels = 1
void LoadInput1(size_t width, const int8_t* values) {
  size_t input_words = 4;
  cfu_set(REG_INPUT_NUM_WORDS, input_words);

  // For each of four consecutive rows, take data from four consecutive pixels
  for (size_t row_index = 0; row_index < 4; row_index++) {
    const int8_t* source = values + (row_index * width);
    cfu_set(REG_SET_INPUT, pack32(source[0], source[1], source[2], source[3]));
  }
}

// Load input when in_channels is divisible by 4
void LoadInputN(size_t width, size_t in_channels, const int8_t* values) {
  const size_t pixels_per_input_row = 4;
  const size_t words_per_input_row =
      pixels_per_input_row * in_channels / BYTES_PER_WORD;
  const size_t bytes_per_width = width * in_channels;
  size_t input_words =
      FILTER_WIDTH * FILTER_HEIGHT * in_channels / BYTES_PER_WORD;
  cfu_set(REG_INPUT_NUM_WORDS, input_words);

  // For each of four consecutive rows, take data from four consecutive pixels
  for (size_t row_index = 0; row_index < 4; row_index++) {
    const uint32_t* source = reinterpret_cast<const uint32_t*>(
        values + (row_index * bytes_per_width));
    for (size_t i = 0; i < words_per_input_row; i++) {
      cfu_set(REG_SET_INPUT, *source++);
    }
  }
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

void LoadFilter(size_t in_channels, size_t out_channels, const int8_t* values) {
  const uint32_t* values_as_words = reinterpret_cast<const uint32_t*>(values);
  size_t filter_words =
      FILTER_WIDTH * FILTER_HEIGHT / 4 * in_channels * out_channels;
  cfu_set(REG_FILTER_NUM_WORDS, filter_words);
  const uint32_t* end = values_as_words + filter_words;
  while (values_as_words != end) {
    cfu_set(REG_SET_FILTER, *values_as_words++);
  }
}

Vector16 GetFilter() {
  uint32_t word0 = cfu_get(REG_FILTER_0);
  uint32_t word1 = cfu_get(REG_FILTER_1);
  uint32_t word2 = cfu_get(REG_FILTER_2);
  uint32_t word3 = cfu_get(REG_FILTER_3);
  return Vector16{{word0, word1, word2, word3}};
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
  uint32_t word0 = cfu_get(REG_INPUT_0);
  uint32_t word1 = cfu_get(REG_INPUT_1);
  uint32_t word2 = cfu_get(REG_INPUT_2);
  uint32_t word3 = cfu_get(REG_INPUT_3);
  return Vector16{{word0, word1, word2, word3}};
}

// Sets per-layer output parameters
void SetOutputOffsets(int32_t output_offset, int32_t output_activation_min,
                      int32_t output_activation_max) {
  cfu_set(REG_OUTPUT_OFFSET, output_offset);
  cfu_set(REG_OUTPUT_MIN, output_activation_min);
  cfu_set(REG_OUTPUT_MAX, output_activation_max);
}

// Loads output parameters
void LoadOutputParams(size_t offset, size_t count, const int32_t* bias_data,
                      const int32_t* output_multiplier,
                      const int32_t* output_shift) {
  cfu_set(REG_OUTPUT_PARAMS_RESET, 1);
  for (size_t i = offset; i < offset + count; i++) {
    cfu_set(REG_OUTPUT_BIAS, bias_data[i]);
    cfu_set(REG_OUTPUT_MULTIPLIER, output_multiplier[i]);
    cfu_set(REG_OUTPUT_SHIFT, output_shift[i]);
  }
}

int32_t MultiplyByQuantizedMultiplier_01(int32_t x, int32_t multiplier,
                                         int shift) {
  using gemmlowp::RoundingDivideByPOT;
  using gemmlowp::SaturatingRoundingDoublingHighMul;
  int right_shift = -shift;
  int32_t product = SaturatingRoundingDoublingHighMul(x, multiplier);
  return RoundingDivideByPOT(product, right_shift);
}

int32_t MultiplyByQuantizedMultiplier_02(int32_t x, int32_t multiplier,
                                         int shift) {
  using gemmlowp::SaturatingRoundingDoublingHighMul;
  int right_shift = -shift;
  int32_t product = SaturatingRoundingDoublingHighMul(x, multiplier);

  // RoundingDivideByPOT implementation
  int32_t quotient = product >> right_shift;
  int32_t mask = (1 << right_shift) - 1;
  int32_t remainder = product & mask;
  int32_t threshold = (mask >> 1) + ((x < 0) ? 1 : 0);
  int32_t rounding = (remainder > threshold) ? 1 : 0;
  return quotient + rounding;
}

int32_t MultiplyByQuantizedMultiplier_03(int32_t x, int32_t multiplier,
                                         int shift) {
  // Saturating Rounding Double High Mul
  int64_t a_64(x);
  int64_t b_64(multiplier);
  int64_t ab_64 = a_64 * b_64;
  int32_t nudge = ab_64 >= 0 ? (1 << 30) : (1 - (1 << 30));
  int32_t product = static_cast<std::int32_t>((ab_64 + nudge) / (1ll << 31));

  // RoundingDivideByPOT implementation
  int right_shift = -shift;
  int32_t quotient = product >> right_shift;
  int32_t mask = (1 << right_shift) - 1;
  int32_t remainder = product & mask;
  int32_t threshold = (mask >> 1) + ((x < 0) ? 1 : 0);
  int32_t rounding = (remainder > threshold) ? 1 : 0;
  return quotient + rounding;
}

int32_t MultiplyByQuantizedMultiplier_04(int32_t x, int32_t multiplier,
                                         int shift) {
  TFLITE_DCHECK(multiplier >= 0x40000000 && multiplier <= 0x7fffffff);
  TFLITE_DCHECK(shift >= -11 && shift <= -3);

  // Saturating Rounding Double High Mul
  bool positive = x > 0;
  int64_t a_64(positive ? x : -x);
  int64_t b_64(multiplier);
  int64_t ab_64 = a_64 * b_64;
  if (positive) {
    ab_64 += (1 << 30);
  } else {
    ab_64 += (1 << 30) - 1;
  }
  int64_t t = ab_64 >> 31;
  int32_t product = static_cast<int32_t>(t);
  if (!positive) {
    product = -product;
  }

  // RoundingDivideByPOT implementation
  int32_t quotient;
  int32_t mask;
  switch (shift) {
    case -3:
      quotient = product >> 3;
      mask = (1 << 3) - 1;
      break;
    case -4:
      quotient = product >> 4;
      mask = (1 << 4) - 1;
      break;
    case -5:
      quotient = product >> 5;
      mask = (1 << 5) - 1;
      break;
    case -6:
      quotient = product >> 6;
      mask = (1 << 6) - 1;
      break;
    case -7:
      quotient = product >> 7;
      mask = (1 << 7) - 1;
      break;
    case -8:
      quotient = product >> 8;
      mask = (1 << 8) - 1;
      break;
    case -9:
      quotient = product >> 9;
      mask = (1 << 9) - 1;
      break;
    case -10:
      quotient = product >> 10;
      mask = (1 << 10) - 1;
      break;
    case -11:
      quotient = product >> 11;
      mask = (1 << 11) - 1;
      break;
    default:
      quotient = 0;
      mask = 0;
      printf("***BAD SHIFT\n");
  }
  int32_t remainder = product & mask;
  int32_t threshold = (mask >> 1) + ((x < 0) ? 1 : 0);
  int32_t rounding = (remainder > threshold) ? 1 : 0;
  return quotient + rounding;
}

// Same functionality. Uses software CFU implementations of operation
int32_t MultiplyByQuantizedMultiplier_SW(int32_t x, int32_t multiplier,
                                         int shift) {
  int32_t product = cfu_op2_sw(MATH_SRDHM, x, multiplier);
  return cfu_op2_sw(MATH_RDBPOT, product, shift);
}

// Same functionality. Uses hard CFU implementations of operations
int32_t MultiplyByQuantizedMultiplier_HW(int32_t x, int32_t multiplier,
                                         int shift) {
  int32_t product = cfu_op2_hw(MATH_SRDHM, x, multiplier);
  return cfu_op2_hw(MATH_RDBPOT, product, shift);
}

};  // namespace hps_accel
