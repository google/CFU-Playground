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

#include "dump.h"

#include <cstdio>

// Dump len bytes of data
void dump_hex(const uint8_t* data, size_t len) {
  for (size_t i = 0; i < len; i++) {
    printf("0x%02x,%c", data[i], (i & 0xf) == 0xf ? '\n' : ' ');
  }
}

// Dump len words of data
void dump_hex(const int32_t* data, size_t len) {
  for (size_t i = 0; i < len; i++) {
    printf("0x%08lx,%c", data[i], (i & 0x3) == 0x3 ? '\n' : ' ');
  }
}
