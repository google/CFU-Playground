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

#include <stdint.h>

uint32_t Cfu(uint32_t functionid, uint32_t rs1, uint32_t rs2)
{
  uint32_t retval = 0;

  if (functionid & 0x2) {
    // bitreverse (rs1)
    for (int i=0; i<32; ++i) {
      retval |= (((rs1 >>i) & 0x1) << (31-i));
    }
  }
  else if (functionid & 0x1) {
    // byte swap (rs1)
    for (int i=0; i<32; i+=8) {
      retval |= (((rs1 >>i) & 0xff) << (24-i));
    }
  } else {
    // byte sum
    retval += (rs1 & 0xff) + (rs2 & 0xff);
    rs1 >>= 8;
    rs2 >>= 8;
    retval += (rs1 & 0xff) + (rs2 & 0xff);
    rs1 >>= 8;
    rs2 >>= 8;
    retval += (rs1 & 0xff) + (rs2 & 0xff);
    rs1 >>= 8;
    rs2 >>= 8;
    retval += (rs1 & 0xff) + (rs2 & 0xff);
  }
  return retval;
}



