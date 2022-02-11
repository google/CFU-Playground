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

// An implementation of MurmurHash as described at 
// https://en.wikipedia.org/wiki/MurmurHash
// 
// It is reimplemented here in order to avoid pulling a small dependency into the build

#ifndef _MURMURHASH_H
#define _MURMURHASH_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Hash len bytes of data
int32_t murmurhash3_32(const uint8_t* data, size_t len);

#ifdef __cplusplus
}
#endif

#endif  // _MURMURHASH_H