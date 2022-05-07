/*
 * Copyright 2022 The CFU-Playground Authors
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

int32_t accumulator;

// Gets a byte as an int8 from the given word
inline int8_t extract_byte(uint32_t word, int num) {
  return static_cast<int8_t>(0xff & (word >> (num * 8)));
}

// Multipy rs1 bytes by rs2 bytes and sum everything together
int32_t multiply_add4(uint32_t rs1, uint32_t rs2){ 
  return (
    (128 + extract_byte(rs1, 0)) * extract_byte(rs2, 0) +
    (128 + extract_byte(rs1, 1)) * extract_byte(rs2, 1) +
    (128 + extract_byte(rs1, 2)) * extract_byte(rs2, 2) +
    (128 + extract_byte(rs1, 3)) * extract_byte(rs2, 3));
}


//
// In this function, place C code to emulate your CFU. You can switch between
// hardware and emulated CFU by setting the CFU_SOFTWARE_DEFINED DEFINE in
// the Makefile.
uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  switch (funct7) {
    case 0:
      accumulator = 0;
      break;
    case 1:
      accumulator += multiply_add4(rs1, rs2);
    default:
      break;
  }
  return static_cast<uint32_t>(accumulator);
}
