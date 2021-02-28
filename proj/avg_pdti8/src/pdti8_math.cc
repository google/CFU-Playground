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

#include "pdti8_math.h"
#include "cfu.h"
// GEMMLOWP
#include "fixedpoint/fixedpoint.h"



int32_t math_srdhm_gemmlowp(int32_t a, int32_t b) {
    return gemmlowp::SaturatingRoundingDoublingHighMul(a, b);
}

int32_t math_srdhm_cfu(int32_t a, int32_t b) {
    return cfu_op7(0, a, b);
}

int32_t math_rdbypot_gemmlowp(int32_t x, int exponent) {
    return gemmlowp::RoundingDivideByPOT(x, exponent);
}

int32_t math_rdbypot_cfu(int32_t x, int exponent) {
    return cfu_op6(0, x, exponent);
}