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

#include "software_cfu.h"

#include <stdint.h>

#include "hps_cfu.h"

namespace {

uint32_t SetRegister(int funct7, uint32_t rs1, uint32_t rs2) { return 0; }
uint32_t GetRegister(int funct7, uint32_t rs1, uint32_t rs2) { return 0; }

};  // namespace

extern "C" uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2) {
  switch (funct3) {
    case 0:
      return SetRegister(funct7, rs1, rs2);
    case 1:
      return GetRegister(funct7, rs1, rs2);
    default:
      return 0;
  }
}
