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
#ifndef _B64_UTIL_H
#define _B64_UTIL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Encode a block in base 64.
// Returns number of chars in output buffer, which will be ceil(len/3) * 4
size_t b64_encode(const int8_t* in, size_t len, char* out);

// Dumps to console
void b64_dump(const int8_t* in, size_t len);

#ifdef __cplusplus
}
#endif

#endif  // _B64_UTIL_H