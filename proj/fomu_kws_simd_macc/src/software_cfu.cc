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

#include <stdint.h>
#include "software_cfu.h"

//
// In this function, place C code to emulate your CFU. You can switch between
// hardware and emulated CFU by setting the CFU_SOFTWARE_DEFINED DEFINE in
// the Makefile.
uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2)
{
  int srs1 = (int)rs1;

  static int input_offset = 0;
  static int acc = 0;

  if (funct3 == 0) input_offset = srs1;

  if (funct3 == 1) acc = rs1;

  if (funct3 == 2) {
      signed char f0 = rs1 & 255;
      signed char f1 = (rs1 >> 8) & 255;
      signed char f2 = (rs1 >> 16) & 255;
      signed char f3 = (rs1 >> 24) & 255;
      signed char i0 = rs2 & 255;
      signed char i1 = (rs2 >> 8) & 255;
      signed char i2 = (rs2 >> 16) & 255;
      signed char i3 = (rs2 >> 24) & 255;

      acc += f0 * (i0 + input_offset) +
             f1 * (i1 + input_offset) +
             f2 * (i2 + input_offset) +
             f3 * (i3 + input_offset);
  }

  return acc;
}
