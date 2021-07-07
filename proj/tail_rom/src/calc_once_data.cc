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

#include "calc_once_data.h"

#include <cstdio>

#include "playground_util/dump.h"
#include "playground_util/murmurhash.h"
#include "playground_util/pause.h"

#define CAPTURE_BEGIN "\n+++ calculate_once::Capture begin +++\n"
#define CAPTURE_END "+++ calculate_once::Capture end +++\n"

namespace calculate_once {

// Reset this this object
void Capturer::Start(const unsigned char* model_data,
                     unsigned int model_length) {
  capturing_ = true;
  printf(CAPTURE_BEGIN);
  printf("// Generated cache data include file\n\n");
  printf("#include \"calc_once_data.h\"\n\n");
  printf("namespace {\n");
  printf("uint32_t model_hash = 0x%08lx;\n",
         murmurhash3_32(model_data, model_length));
  printf(CAPTURE_END);
  sequence_counter_ = 0;
}

// Capture an area of memory
void Capturer::Capture(const int32_t* data, size_t num_words) {
  if (!capturing_) {
    return;
  }

  // Capture as uint32_t to allow data to be capture in hex. The hex format is
  // more convenient for debugging.
  printf(CAPTURE_BEGIN);
  printf("const uint32_t buffer_%d[%d] = {\n", sequence_counter_, num_words);
  dump_hex(data, num_words);
  printf("};\n");
  printf("constexpr size_t size_%d = %d;\n", sequence_counter_, num_words);
  printf(CAPTURE_END);
  sequence_counter_++;
}

void Capturer::Finish() {
  if (!capturing_) {
    return;
  }
  pause();
  printf(CAPTURE_BEGIN);
  printf("const int32_t* buffers[] = {\n");
  for (size_t i = 0; i < sequence_counter_; i++) {
    printf("  reinterpret_cast<const int32_t *>(buffer_%d),\n", i);
  }
  printf("};\n");

  pause();
  printf("const size_t sizes[] = {\n");
  for (size_t i = 0; i < sequence_counter_; i++) {
    printf("  size_%d,\n", i);
  }
  printf("};\n");

  printf("} // anonymous namespace\n\n");
  // __CACHE_NAME__ is replaced with the cache name, later
  printf("calculate_once::Cache *GetCache__CACHE_NAME__() {\n");
  printf(
      "  static calculate_once::Cache cache(model_hash, %d, buffers, sizes);\n",
      sequence_counter_);
  printf("  return &cache;\n");
  printf("};\n");
  printf(CAPTURE_END);

  capturing_ = false;
}

Capturer capturer;

bool Cache::InitForModel(const unsigned char* model_data,
                         unsigned int model_length) {
  // By default, don't use cache
  use_ = false;

  // If buffers are not set, do not use. (probably the empty default object)
  if (!buffers_) {
    return false;
  }

  // Check whether hash matches
  uint32_t hash = murmurhash3_32(model_data, model_length);
  if (hash != model_hash_) {
    return false;
  }

  // Use it, if it matches
  use_ = true;
  next_ = 0;
  return true;
}

int32_t* Cache::FetchNextBuffer(size_t num_words) {
  if (!use_) {
    return NULL;
  }

  if (next_ >= num_buffers_) {
    printf("Asked for buffer #%u, but only %u available\n", next_,
           num_buffers_);
    next_++;
    return NULL;
  }

  if (sizes_[next_] != num_words) {
    printf("%d: Expected request for size %u, but was %u\n", next_,
           sizes_[next_], num_words);
    next_++;
    return NULL;
  }

  // Cast away const for compatibility
  return const_cast<int32_t*>(buffers_[next_++]);
}

// Empty cache is never able to be used by allocators
Cache empty_cache(0, 0, nullptr, nullptr);

Cache* current_cache = NULL;

void SetCache(Cache* cache) { current_cache = cache; }

// Returns the current cache object. Will return an empty default object if no
// cache is set.
Cache* GetCache() { return current_cache ? current_cache : &empty_cache; }

}  // namespace calculate_once