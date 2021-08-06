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

#define RESET_ACC() cfu_op0(1, 0, 0)
#define SIMD_MAC(input_val, filter_val) cfu_op0(0, input_val, filter_val)
#define MAC(input_val, filter_val) cfu_op1(0, input_val, filter_val)

#define RESET_ACC_SW() cfu_op0_sw(1, 0, 0)
#define SIMD_MAC_SW(input_val, filter_val) cfu_op0_sw(0, input_val, filter_val)
#define MAC_SW(input_val, filter_val) cfu_op1_sw(0, input_val, filter_val)

#define RESET_ACC_HW() cfu_op0_hw(1, 0, 0)
#define SIMD_MAC_HW(input_val, filter_val) cfu_op0_hw(0, input_val, filter_val)
#define MAC_HW(input_val, filter_val) cfu_op1_hw(0, input_val, filter_val)

#endif  // KWS_CFU_H
