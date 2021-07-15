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

#include "playground_util/random.h"

// See
// https://en.wikipedia.org/wiki/Linear_congruential_generator#Parameters_in_common_use
static const int64_t rand_a = 6364136223846793005;
static const int64_t rand_c = 1442695040888963407;
int32_t next_pseudo_random(int64_t* r) {
  *r = (*r) * rand_a + rand_c;
  // Use higher order bits
  return *r >> 28;
}