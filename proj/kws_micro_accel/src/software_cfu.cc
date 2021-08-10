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

#include "fixedpoint/fixedpoint.h"

uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  static int32_t acc = 0;

  switch (funct3) {
    case 0x1: {  // Optionally SIMD MAC.
      int8_t end_idx = funct7 & 0x1 ? 4 : 1;
      int32_t input_offset = funct7 & 0x2 ? -83 : 128;
      for (int i = 0; i < end_idx; i++) {
        acc += (static_cast<int8_t>((rs1 >> i * 8) & 0xff) + input_offset) *
               static_cast<int8_t>((rs2 >> i * 8) & 0xff);
      }
      break;
    }
    case 0x2: {  // Half of gemmlowp::SaturatingRoundingDoublingHighMul.
      int64_t acc_64 = static_cast<int64_t>(rs1) << 32 | rs2;
      int32_t nudge = acc_64 >= 0 ? (1 << 30) : (1 - (1 << 30));
      acc = static_cast<int32_t>((acc_64 + nudge) / (1ll << 31));
      break;
    }
    case 0x4: {  // Rounding, clamping divide by power of two.
      acc = gemmlowp::RoundingDivideByPOT(acc, -static_cast<int>(rs2));
      acc -= 128;
      acc = (acc > 127) ? 127 : (acc < -128) ? -128 : acc;
      break;
    }
    default: {  // Reset.
      acc = 0;
      break;
    }
  }

  return static_cast<uint32_t>(acc);
}
