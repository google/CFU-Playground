// Copyright 2021 The CFU-Playground Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <calc_once_data.h>

#include <cstdio>

#include "playground_util/dump.h"
#include "playground_util/murmurhash.h"

#define CAPTURE_BEGIN "\n+++ calculate_once Capture begin +++\n"
#define CAPTURE_END "+++ calculate_once Capture end +++\n"

namespace calculate_once {

// Reset this this object
void Capturer::Reset(const unsigned char* model_data,
                     unsigned int model_length) {
                         if (!enabled_) {return;}
  printf(CAPTURE_BEGIN "captured.SetHash(0x%08lx);\n" CAPTURE_END,
         murmurhash3_32(model_data, model_length));
  sequence_counter_ = 0;
}

// Capture an area of memory
void Capturer::Capture(const int32_t* data, size_t num_words) {
                         if (!enabled_) {return;}

  printf(CAPTURE_BEGIN);
  printf("captured.SetBuffer(%d, int32_t[] {", sequence_counter_);
  dump_hex(reinterpret_cast<const uint8_t*>(data), num_words * 4);
  printf("}, %d)", num_words);
  printf(CAPTURE_END);
  sequence_counter_++;
}

Capturer capturer;

}  // namespace calculate_once