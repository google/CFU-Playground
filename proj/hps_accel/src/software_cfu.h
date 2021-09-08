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

#ifndef SOFTWARE_CFU_H
#define SOFTWARE_CFU_H

#include <cstddef>
#include <cstdint>
#include <cstdio>

#include "gateware_constants.h"

namespace soft_cfu {

// Multiply-accumulate unit
extern int32_t macc_input_offset;
extern int8_t macc_input[16];
extern int8_t macc_filter[16];

inline void Unpack32(int8_t* dest, uint32_t value) {
  dest[0] = (value & 0x000000ff);
  dest[1] = (value & 0x0000ff00) >> 8;
  dest[2] = (value & 0x00ff0000) >> 16;
  dest[3] = (value & 0xff000000) >> 24;
}

inline void SetMaccInput(size_t n, uint32_t value) {
  Unpack32(macc_input + (4 * n), value);
}
inline void SetMaccFilter(size_t n, uint32_t value) {
  Unpack32(macc_filter + (4 * n), value);
}

// Do the macc
inline int32_t Macc() {
  int32_t macc_out = 0;
  // NOTE: unrolling this resulted in slower execution
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
    if (index >= len) {
      index = len - 4;
    }
  }
  uint32_t Get(size_t n) {
    return data[index + n];
  }
  void Next() {
    index = (index + 4) % len;
  }

 private:
  uint32_t data[MAX_STORAGE_WORDS];
  size_t len;
  size_t index;
};

extern Storage filter_storage;
extern Storage input_storage;

// Verify register storage
extern uint32_t reg_verify;

inline uint32_t SetRegister(int funct7, uint32_t rs1, uint32_t rs2) {
  switch (funct7) {
    case REG_RESET:
      filter_storage.Reset(0);
      return 0;
    case REG_FILTER_NUM_WORDS:
      filter_storage.Reset(rs1);
      return 0;
    case REG_INPUT_NUM_WORDS:
      input_storage.Reset(rs1);
      return 0;
    case REG_INPUT_OFFSET:
      macc_input_offset = rs1;
      return 0;
    case REG_SET_FILTER:
      filter_storage.Store(rs1);
      return 0;
    case REG_SET_INPUT:
      input_storage.Store(rs1);
      return 0;
    case REG_FILTER_INPUT_NEXT:
      filter_storage.Next();
      input_storage.Next();
      return 0;
    case REG_VERIFY:
      reg_verify = rs1;
      return 0;

    default:
      printf("\nInvalid SetRegister number %d\n", funct7);
      return 0;
  }
  return 0;
}

inline uint32_t GetRegister(int funct7, uint32_t rs1, uint32_t rs2) {
  switch (funct7) {
    case REG_FILTER_0:
      return filter_storage.Get(0);
    case REG_FILTER_1:
      return filter_storage.Get(1);
    case REG_FILTER_2:
      return filter_storage.Get(2);
    case REG_FILTER_3:
      return filter_storage.Get(3);
    case REG_INPUT_0:
      return input_storage.Get(0);
    case REG_INPUT_1:
      return input_storage.Get(1);
    case REG_INPUT_2:
      return input_storage.Get(2);
    case REG_INPUT_3:
      return input_storage.Get(3);
    case REG_MACC_OUT:
      SetMaccFilter(0, filter_storage.Get(0));
      SetMaccFilter(1, filter_storage.Get(1));
      SetMaccFilter(2, filter_storage.Get(2));
      SetMaccFilter(3, filter_storage.Get(3));
      SetMaccInput(0, input_storage.Get(0));
      SetMaccInput(1, input_storage.Get(1));
      SetMaccInput(2, input_storage.Get(2));
      SetMaccInput(3, input_storage.Get(3));
      return Macc();
    case REG_VERIFY:
      return reg_verify + 1;
    default:
      printf("\nInvalid GetRegister number %d\n", funct7);
      return 0;
  }
}

extern uint32_t ping_storage;

inline uint32_t Ping(uint32_t rs1, uint32_t rs2) {
  uint32_t result = ping_storage;
  ping_storage = rs1 + rs2;
  return result;
}

};  // namespace soft_cfu

inline uint32_t software_cfu(int funct3, int funct7, uint32_t rs1,
                             uint32_t rs2) {
  switch (funct3) {
    case INS_SET:
      return soft_cfu::SetRegister(funct7, rs1, rs2);
    case INS_GET:
      return soft_cfu::GetRegister(funct7, rs1, rs2);
    case INS_PING:
      return soft_cfu::Ping(rs1, rs2);
    default:
      return 0;
  }
}

#endif  // SOFTWARE_CFU_H
