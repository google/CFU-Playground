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

#include "b64_util.h"

#include <stdio.h>

#include "cfu.h"

static const char* b64_table =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static inline char b64_lookup(char n) { return b64_table[0x3f & n]; }

size_t b64_encode(const int8_t* in, size_t len, char* out) {
  size_t out_len = 0;
  const int8_t* end = in + len;
  while (end - in >= 3) {
    *(out++) = b64_lookup(in[0] >> 2);
    *(out++) = b64_lookup(in[0] << 4 | (0xf & in[1] >> 4));
    *(out++) = b64_lookup(in[1] << 2 | (0x3 & in[2] >> 6));
    *(out++) = b64_lookup(in[2]);
    in += 3;
    out_len += 4;
  }
  if (end - in == 2) {
    *(out++) = b64_lookup(in[0] >> 2);
    *(out++) = b64_lookup(in[0] << 4 | (0xf & in[1] >> 4));
    *(out++) = b64_lookup(in[1] << 2);
    *(out++) = '=';
    out_len += 4;
  } else if (end - in == 1) {
    *(out++) = b64_lookup(in[0] >> 2);
    *(out++) = b64_lookup(in[0] << 4);
    *(out++) = '=';
    *(out++) = '=';
    out_len += 4;
  }
  return out_len;
}

static inline void delay() {
  for (int i = 0; i < 100000; i++) {
    // nop
    __asm__ __volatile__("add zero, zero, zero");
  }
}

void b64_dump(const int8_t* in, size_t len) {
  printf("len %u\n");
  char buf[81];
  while (len > 0) {
    const size_t batch = len >= 60 ? 60 : len;
    const size_t out_len = b64_encode(in, batch, buf);
    buf[out_len] = 0;
    puts(buf);
    delay();
    in += batch;
    len -= batch;
  }
}
