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

#include "murmurhash.h"

int32_t murmurhash3_32(const uint8_t* data, size_t len) {
  // Description of algorithm copied from
  // https://en.wikipedia.org/wiki/MurmurHash#Algorithm
  // algorithm Murmur3_32 is
  //     // Note: In this version, all arithmetic is performed with unsigned
  //              32-bitintegers.
  //     //       In the case of overflow, the result is reduced modulo 232.
  // input: key, len, seed

  // c1 ← 0xcc9e2d51
  // c2 ← 0x1b873593
  // r1 ← 15
  // r2 ← 13
  // m ← 5
  // n ← 0xe6546b64
  uint32_t c1 = 0xcc9e2d51;
  uint32_t c2 = 0x1b873593;
  size_t r1 = 15;
  size_t r2 = 13;
  uint32_t m = 5;
  uint32_t n = 0xe6546b64;

  // hash ← seed
  uint32_t hash = 0;

  // for each fourByteChunk of key do
  const uint32_t* chunkp = reinterpret_cast<const uint32_t*>(data);
  const uint32_t* endp = chunkp + (len / 4);
  for (; chunkp != endp; chunkp++) {
    //     k ← fourByteChunk
    uint32_t k = *chunkp;

    //     k ← k × c1
    //     k ← k ROL r1
    //     k ← k × c2
    k = k * c1;
    k = (k << r1) | (k >> (32 - r1));
    k = k * c2;

    //     hash ← hash XOR k
    //     hash ← hash ROL r2
    //     hash ← (hash × m) + n
    hash = hash ^ k;
    hash = (hash << r2) | (hash >> (32 - r2));
    hash = hash * m + n;
  }

  // with any remainingBytesInKey do
  uint32_t remaining = 0;
  for (size_t i = 0; i < len % 4; i++) {
    remaining += data[len / 4 * 4 + i] << (8 * i);
  }
  //     remainingBytes ← SwapToLittleEndian(remainingBytesInKey)
  //     // Note: Endian swapping is only necessary on big-endian machines.
  //     //       The purpose is to place the meaningful digits towards the low
  //     end of the value,
  //     //       so that these digits have the greatest potential to affect the
  //     low range digits
  //     //       in the subsequent multiplication.  Consider that locating the
  //     meaningful digits
  //     //       in the high range would produce a greater effect upon the high
  //     digits of the
  //     //       multiplication, and notably, that such high digits are likely
  //     to be discarded
  //     //       by the modulo arithmetic under overflow.  We don't want that.

  //     remainingBytes ← remainingBytes × c1
  //     remainingBytes ← remainingBytes ROL r1
  //     remainingBytes ← remainingBytes × c2
  remaining = remaining * c1;
  remaining = (remaining << r1) | (remaining >> (32 - r1));
  remaining =  remaining * c2;

  //     hash ← hash XOR remainingBytes
  hash = hash ^ remaining;

  // hash ← hash XOR len
  hash = hash ^ len;

  // hash ← hash XOR (hash >> 16)
  // hash ← hash × 0x85ebca6b
  // hash ← hash XOR (hash >> 13)
  // hash ← hash × 0xc2b2ae35
  // hash ← hash XOR (hash >> 16)
  hash = hash ^ (hash >> 16);
  hash = hash * 0x85ebca6b;
  hash = hash ^ (hash >> 13);
  hash = hash * 0xc2b2ae35;
  hash = hash ^ (hash >> 16);

  return hash;
}