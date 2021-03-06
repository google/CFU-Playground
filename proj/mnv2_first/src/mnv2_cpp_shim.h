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
#ifndef _MNV2_CPP_SHIM_H
#define _MNV2_CPP_SHIM_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Shim functions to make C++ functionality available to C

int32_t mul_by_quantized_mul(int32_t x, int32_t quantized_multiplier,
                             int shift);

#ifdef __cplusplus
}
#endif
#endif  // _MNV2_CPP_SHIM_H