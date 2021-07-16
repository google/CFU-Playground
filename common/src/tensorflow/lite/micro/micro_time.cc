/* Copyright 2020 The TensorFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#include "tensorflow/lite/micro/micro_time.h"

// Read the cycle counter.
//
// The value of the counter is stored across two 32-bit registers: `mcycle` and
// `mcycleh`. This function is guaranteed to return a valid 64-bit cycle
// counter value, even if `mcycle` overflows before reading `mcycleh`.
//
// Adapted from: The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA
// V20191213, pp. 61.
static inline uint64_t get_mcycle() {
  uint32_t cycle_low = 0;
  uint32_t cycle_high = 0;
  uint32_t cycle_high_2 = 0;
  asm volatile(
      "read%=:"
      "  csrr %0, mcycleh;"     // Read `mcycleh`.
      "  csrr %1, mcycle;"      // Read `mcycle`.
      "  csrr %2, mcycleh;"     // Read `mcycleh` again.
      "  bne  %0, %2, read%=;"  // Try again if `mcycle` overflowed before
                                // reading `mcycleh`.
      : "+r"(cycle_high), "=r"(cycle_low), "+r"(cycle_high_2)
      :);
  return (uint64_t) cycle_high << 32 | cycle_low;
}

namespace tflite {

// Assumes 100 MHz
int32_t ticks_per_second() { return 100000000 / 1024; }

// 1 "tick" = 1024 clock cycles
int32_t GetCurrentTimeTicks() { return get_mcycle() >> 10; }

}  // namespace tflite
