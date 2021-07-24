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

namespace {

uint32_t byte_sum(uint32_t rs1, uint32_t rs2) {
  uint32_t retval = 0;
  for (int i = 0; i < 4; i++) {
    retval += (rs1 & 0xff) + (rs2 & 0xff);
    rs1 >>= 8;
    rs2 >>= 8;
  }
  return retval;
}

uint32_t byte_swap(uint32_t rs1) {
  uint32_t retval = 0;
  for (int i = 0; i < 32; i += 8) {
    retval |= (((rs1 >> i) & 0xff) << (24 - i));
  }
  return retval;
}

uint32_t bit_reverse(uint32_t rs1) {
  uint32_t retval = 0;
  for (int i = 0; i < 32; ++i) {
    retval |= (((rs1 >> i) & 0x1) << (31 - i));
  }
  return retval;
}

uint32_t fib(uint32_t rs1) {
  if (rs1 > 46) {
    return 0;
  }

  uint32_t s1 = 1, s2 = 1;

  for (uint32_t count = rs1; count > 0; --count) {
    uint32_t sum = s1 + s2;
    s1 = s2;
    s2 = sum;
  }

  return s1;
}
};  // anonymous namespace

// In this function, place C code to emulate your CFU. You can switch between
// hardware and emulated CFU by setting the CFU_SOFTWARE_DEFINED DEFINE in
// the Makefile.
uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  switch (funct3) {
    case 0:
      return byte_sum(rs1, rs2);
    case 1:
      return byte_swap(rs1);
    case 2:
      return bit_reverse(rs1);
    case 3:
      return fib(rs1);
    default:
      return 0;
  }
}
