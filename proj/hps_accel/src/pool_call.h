/*
 * Copyright 2022 The CFU-Playground Authors
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

#ifndef _POOL_CALL_H
#define _POOL_CALL_H

#include <cstdint>

// Functionality for calling MaxPool from a test harnesses

struct PoolData {
  const char* name;
  const uint8_t* params;
  const uint8_t* input_shape;
  const uint8_t* input_data;
  const uint8_t* output_shape;
  const uint8_t* output_data;
};

// Tests MaxPool with the data in the given structure
void test_pool(const PoolData* data);

#endif  // _POOL_CALL_H