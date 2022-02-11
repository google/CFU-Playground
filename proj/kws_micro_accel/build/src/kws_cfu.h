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

#ifndef KWS_CFU_H
#define KWS_CFU_H

#include "cfu.h"

#define RESET_ACC() cfu_op0(0, 0, 0)
#define MAC(input, filter) cfu_op1(0, input, filter)
#define MAC_LAYER_ONE(input, filter) cfu_op1(2, input, filter)
#define SIMD_MAC(inputs, filters) cfu_op1(1, inputs, filters)
#define ROUNDING_DOUBLE_HIGH(top, bottom) cfu_op2(0, top, bottom)
#define ROUNDING_CLAMPING_DIVIDE_BY_POT(shift) cfu_op4(0, 0, shift)

#define RESET_ACC_SW() cfu_op0_sw(0, 0, 0)
#define MAC_SW(input, filter) cfu_op1_sw(0, input, filter)
#define MAC_LAYER_ONE_SW(input, filter) cfu_op1_sw(2, input, filter)
#define SIMD_MAC_SW(inputs, filters) cfu_op1_sw(1, inputs, filters)
#define ROUNDING_DOUBLE_HIGH_SW(top, bottom) cfu_op2_sw(0, top, bottom)
#define ROUNDING_CLAMPING_DIVIDE_BY_POT_SW(shift) cfu_op4_sw(0, 0, shift)

#define RESET_ACC_HW() cfu_op0_hw(0, 0, 0)
#define MAC_HW(input, filter) cfu_op1_hw(0, input, filter)
#define MAC_LAYER_ONE_HW(input, filter) cfu_op1_hw(2, input, filter)
#define SIMD_MAC_HW(inputs, filters) cfu_op1_hw(1, inputs, filters)
#define ROUNDING_DOUBLE_HIGH_HW(top, bottom) cfu_op2_hw(0, top, bottom)
#define ROUNDING_CLAMPING_DIVIDE_BY_POT_HW(shift) cfu_op4_hw(0, 0, shift)

// Implements TFLM's MultiplyByQuantizedMultiplier function using CFU ops.
inline int32_t KwsMultiplyByQuantizedMultiplier(int32_t acc, int32_t q_mult,
                                                int shift) {
  uint32_t top, bottom;
  asm("mul  %[bottom], %[acc], %[q_mult]"
      : [bottom] "=r"(bottom)
      : [acc] "r"(acc), [q_mult] "r"(q_mult));
  asm("mulh %[top], %[acc], %[q_mult]"
      : [top] "=r"(top)
      : [acc] "r"(acc), [q_mult] "r"(q_mult));
  ROUNDING_DOUBLE_HIGH(top, bottom);
  return ROUNDING_CLAMPING_DIVIDE_BY_POT(shift);
}

#endif  // KWS_CFU_H
