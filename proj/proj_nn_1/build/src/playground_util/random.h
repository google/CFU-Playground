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

#ifndef _PLAYGROUND_UTIL_PLAYGROUND_UTIL_RANDOM_H
#define _PLAYGROUND_UTIL_RANDOM_H
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Produces pseudo random 32 bit numbers, using 64 bits of state.
int32_t next_pseudo_random(int64_t* r);

#ifdef __cplusplus
}
#endif

#endif  // _PLAYGROUND_UTIL_RANDOM_H
