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

#include "playground_util/pause.h"

// Dump len bytes of data
void dump_hex(const uint8_t* data, size_t len) {
  for (size_t i = 0; i < len; i++) {
    if ((i & 0x3ff) == 0) {
      pause();
    }
    printf((i & 0xf) == 0 ? "  " : " ");
    printf("0x%02x,", data[i]);
    if ((i & 0xf) == 0xf || (i == len - 1)) {
      printf("\n");
    }
  }
}

// Dump len words of data
void dump_hex(const int32_t* data, size_t len) {
  for (size_t i = 0; i < len; i++) {
    if ((i & 0xff) == 0) {
      pause();
    }
    printf((i & 0x3) == 0 ? "  " : " ");
    printf("0x%08lx,", data[i]);
    if ((i & 0x3) == 0x3 || (i == len - 1)) {
      printf("\n");
    }
  }
}

// Dumps memory as a C array
void dump_c_array(const char* name, const void* data, size_t len) {
  const uint8_t* ptr = static_cast<const uint8_t*>(data);
  printf("const uint8_t %s[] = {", name);
  for (size_t i = 0; i < len; i++) {
    if ((i & 0x3ff) == 0) {
      pause();
    }
    // 16 bytes per line
    if ((i & 0xf) == 0) {
      printf("\n  ");
    }
    printf("0x%02x,", ptr[i]);
  }
  printf("\n};\n");
}
