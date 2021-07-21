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

#include <cstddef>
#include <cstdint>
#include <cstdio>

#include "hps_cfu.h"
#include "software_cfu.h"

namespace {

// Multiply-accumulate unit
int32_t macc_input_offset;
int8_t macc_input[16];
int8_t macc_filter[16];

void Unpack32(int8_t* dest, uint32_t value) {
  dest[0] = (value & 0x000000ff);
  dest[1] = (value & 0x0000ff00) >> 8;
  dest[2] = (value & 0x00ff0000) >> 16;
  dest[3] = (value & 0xff000000) >> 24;
}

void SetMaccInput(size_t n, uint32_t value) {
  Unpack32(macc_input + (4 * n), value);
}
void SetMaccFilter(size_t n, uint32_t value) {
  Unpack32(macc_filter + (4 * n), value);
}

// Do the macc
int32_t Macc() {
  int32_t macc_out = 0;
  // NOTE: obvious optimization is to unroll these loops
  for (size_t n = 0; n < 16; n++) {
    macc_out += (macc_input[n] + macc_input_offset) * macc_filter[n];
  }
  return macc_out;
}

// Very simple storage class.
// TODO: wrap around at calculated point instead of at end of data
// TODO: allow input data to be double-buffered
#define MAX_STORAGE_WORDS 16384
class Storage {
 public:
  void Reset(size_t num_words) {
    len = num_words;
    index = 0;
  }
  void Store(uint32_t value) {
    data[index++] = value;
  }
  uint32_t Get(size_t n) {
    if (index >= len) {
      index = 0;
    }
    uint32_t result = data[index + n];
    if (n == 3) {
      index += 4;
    }
    return result;
  }

 private:
  uint32_t data[MAX_STORAGE_WORDS];
  size_t len;
  size_t index;
};

Storage filter_storage;
// Storage input_storage;

uint32_t SetRegister(int funct7, uint32_t rs1, uint32_t rs2) {
  switch (funct7) {
    case REG_RESET:
      filter_storage.Reset(0);
      return 0;
    case REG_FILTER_NUM_WORDS:
      filter_storage.Reset(rs1);
      return 0;
    case REG_INPUT_NUM_WORDS:
      //
      return 0;
    case REG_INPUT_OFFSET:
      macc_input_offset = rs1;
      return 0;
    case REG_SET_FILTER:
      filter_storage.Store(rs1);
      return 0;
    case REG_MACC_INPUT_0:
      SetMaccInput(0, rs1);
      return 0;
    case REG_MACC_INPUT_1:
      SetMaccInput(1, rs1);
      return 0;
    case REG_MACC_INPUT_2:
      SetMaccInput(2, rs1);
      return 0;
    case REG_MACC_INPUT_3:
      SetMaccInput(3, rs1);
      return 0;
    case REG_MACC_FILTER_0:
      SetMaccFilter(0, rs1);
      return 0;
    case REG_MACC_FILTER_1:
      SetMaccFilter(1, rs1);
      return 0;
    case REG_MACC_FILTER_2:
      SetMaccFilter(2, rs1);
      return 0;
    case REG_MACC_FILTER_3:
      SetMaccFilter(3, rs1);
      return 0;

    default:
      printf("\nInvalid SetRegister number %d\n", funct7);
      return 0;
  }
  return 0;
}

uint32_t GetRegister(int funct7, uint32_t rs1, uint32_t rs2) {
  switch (funct7) {
    case REG_FILTER_0:
      return filter_storage.Get(0);
    case REG_FILTER_1:
      return filter_storage.Get(1);
    case REG_FILTER_2:
      return filter_storage.Get(2);
    case REG_FILTER_3:
      return filter_storage.Get(3);
    case REG_MACC_OUT:
      return Macc();
    default:
      printf("\nInvalid GetRegister number %d\n", funct7);
      return 0;
  }
}

};  // namespace

extern "C" uint32_t software_cfu(int funct3, int funct7, uint32_t rs1,
                                 uint32_t rs2) {
  switch (funct3) {
    case 0:
      return SetRegister(funct7, rs1, rs2);
    case 1:
      return GetRegister(funct7, rs1, rs2);
    default:
      return 0;
  }
}
