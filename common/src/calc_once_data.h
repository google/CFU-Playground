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

#ifndef _CALC_ONCE_DATA_H
#define _CALC_ONCE_DATA_H

#include <cstddef>
#include <cstdint>

// Functions to support capturing, storing and returning data that can be
// calculated once and placed into ROM.

namespace calculate_once {

// The capturer outputs (via printf) each permanent data buffer
class Capturer {
 public:
  Capturer() : enabled_(false), sequence_counter_(0){};
  virtual ~Capturer(){};

  // Reset this this object
  void Reset(const unsigned char* model_data, unsigned int model_length);

  // Capture an area of memory
  void Capture(const int32_t* data, size_t num_words);

  // Enable or Disable
  void Enable(bool enable) { enabled_ = enable; }

 private:
  // Whether capturing is happening
  bool enabled_;

  // The sequence of capturing.
  int sequence_counter_;
};

extern Capturer capturer;

}  // namespace calculate_once

#endif  // _CALC_ONCE_DATA_H