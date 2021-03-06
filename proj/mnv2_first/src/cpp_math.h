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
#ifndef _CPP_MATH_H
#define _CPP_MATH_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// C++ (and other) math functions for C

int32_t cpp_math_mul_by_quantized_mul_software(int32_t x, int32_t quantized_multiplier,
                             int shift);

int32_t cpp_math_mul_by_quantized_mul_gateware1(int32_t x, int32_t quantized_multiplier,
                             int shift);

int32_t cpp_math_mul_by_quantized_mul_gateware2(int32_t x, int32_t quantized_multiplier,
                             int shift);

int32_t cpp_math_srdhm_software(int32_t a, int32_t b);

// Rounding divide by power of two
int32_t cpp_math_rdbpot_software(int32_t value, int shift);

#ifdef __cplusplus
}
#endif
#endif  // _CPP_MATH_H