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

#include "blocks_test.h"

#include <cstdio>

#include "blocks.h"

using hps_accel::multiply_accumulate;
using hps_accel::Vector16;

namespace {

void print(Vector16 m) {
  for (size_t y = 0; y < 4; y++) {
    for (size_t x = 0; x < 4; x++) {
      printf(" %4d", m.get(y * 4 + x));
    }
    printf("\n");
  }
}

bool test_multiply(Vector16 input, Vector16 filter, int32_t input_offset,
                   int32_t expected) {
  printf(".");
  int32_t actual = multiply_accumulate(input, filter, input_offset);
  if (actual == expected) {
    return true;
  }

  printf("\n FAIL\ninput:\n");
  print(input);
  printf("filter:\n");
  print(filter);
  printf("input_offset: %4ld\n", input_offset);
  printf("actual:       %4ld\n", actual);
  printf("expected:     %4ld\n", expected);
  return false;
}

};  // anonymous namespace

extern "C" void do_test_blocks_multiply_accumulate(void) {
  struct {
    Vector16 input;
    Vector16 filter;
    int32_t input_offset;
    int32_t expected;
  } multiply_cases[]{
      // Sum 0^2..15^2
      {Vector16::build(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15),
       Vector16::build(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), 0,
       1240},
      // Introduce input offset
      {Vector16::build(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15),
       Vector16::build(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15),
       12, 2680},
      // Arbitary numbers: case 1
      {Vector16::build(-64, -94, -28, -5, -50, 113, -38, -104, 15, -103, 101,
                       -30, -40, -48, -88, -40),
       Vector16::build(-123, -77, 2, 100, 118, -45, 3, 97, 66, -16, -88, 0, 49,
                       94, 68, 116),
       22, -21971},
      // Arbitary numbers: case 2
      {Vector16::build(-93, 46, -5, -32, -28, 79, 84, 57, 124, 114, 47, -75,
                       -77, -91, 7, 92),
       Vector16::build(-86, 39, 120, -60, 10, -7, 2, -88, -23, -69, 106, 36,
                       -52, -36, -80, -31),
       93, -19504},
  };

  size_t cases = 0;
  size_t failures = 0;
  for (auto m : multiply_cases) {
    cases++;
    if (!test_multiply(m.input, m.filter, m.input_offset, m.expected))
      failures++;
  }
  printf("\n%s: %d cases with %d failures\n", failures ? "FAIL" : "OK", cases,
         failures);
}