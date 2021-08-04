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

// Emulates [SIMD] MAC CFU in software.
uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  static int32_t acc = 0;
  if (funct7 & 0x1) {
    acc = 0;
  } else {
    int8_t end_idx = funct3 & 0x1 ? 1 : 4;

    for (int i = 0; i < end_idx; i++) {
      acc += ((int8_t)((rs1 >> i * 8) & 0xFF) + 128) *
             (int8_t)((rs2 >> i * 8) & 0xFF);
    }
  }
  return (uint32_t)acc;
}
