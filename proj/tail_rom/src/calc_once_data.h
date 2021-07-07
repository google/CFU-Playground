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
  Capturer() : capturing_(false), sequence_counter_(0){};
  virtual ~Capturer(){};

  // Reset this this object
  void Start(const unsigned char* model_data, unsigned int model_length);

  // Capture an area of memory
  void Capture(const int32_t* data, size_t num_words);

  // Finish capturing data
  void Finish();

 private:
  // Whether capturing is happening
  bool capturing_;

  // The sequence of capturing.
  size_t sequence_counter_;
};

extern Capturer capturer;

class Cache {
 public:
  Cache(uint32_t model_hash, size_t num_buffers, const int32_t** buffers,
        const size_t* sizes)
      : model_hash_(model_hash),
        num_buffers_(num_buffers),
        buffers_(buffers),
        sizes_(sizes),
        use_(false),
        next_(0) {}
  virtual ~Cache(){};

  // Initialize cache for given model.
  // Returns false if model does not match, and then marks the cache as "don't
  // use"
  bool InitForModel(const unsigned char* model_data, unsigned int model_length);

  // Fetch the next buffer of captured data
  // Returns NULL if all buffers have already been returned or if num_words does
  // not match the next buffer's size.
  int32_t* FetchNextBuffer(size_t num_words);

 private:
  // Hash of the model to which this cache applies
  uint32_t model_hash_;

  // The number of buffers cached
  size_t num_buffers_;

  // An array of pointers to the cached buffers
  int32_t const** buffers_;

  // An array of sizes of the buffers
  size_t const* sizes_;

  // Whether this cache should be used
  bool use_;

  // Index of the next buffer to be retrieved
  size_t next_;
};

// Sets the current cache - set to null to use default (empty) cache.
void SetCache(Cache* cache);

// Returns the current cache object. Will return an empty default object if no
// cache is set.
Cache* GetCache();

}  // namespace calculate_once

#endif  // _CALC_ONCE_DATA_H