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
#ifndef PDTI8_MATH_H_
#define PDTI8_MATH_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int32_t math_srdhm_gemmlowp(int32_t a, int32_t b);
int32_t math_srdhm_cfu(int32_t a, int32_t b);

int32_t math_rdbypot_gemmlowp(int32_t x, int exponent);
int32_t math_rdbypot_cfu(int32_t x, int exponent);

#ifdef __cplusplus
}
#endif
#endif