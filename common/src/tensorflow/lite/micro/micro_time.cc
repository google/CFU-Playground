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

static inline unsigned get_mcycle() {
  unsigned result;
  asm volatile("csrr %0, mcycle" : "=r"(result));
  return result;
}

static inline void set_mcycle(unsigned cyc) {
  asm volatile("csrw mcycle, %0" ::"r"(cyc));
}

namespace tflite {

// Assumes 100 MHz
int32_t ticks_per_second() { return 100000000; }

// WARNING (from tcal) -- very susceptible to wrap-around (happens every 40s)
//   --> need to get mcycleh, and shift/divide down
//
int32_t GetCurrentTimeTicks() { return (int32_t)get_mcycle(); }

}  // namespace tflite
