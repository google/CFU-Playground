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

#include "software_cfu.h"

#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace soft_cfu {

// Just defines state - all functions are inline
int32_t macc_input_offset;
int8_t macc_input[16];
int8_t macc_filter[16];
uint32_t iterations;

Storage filter_storage;
Storage input_storage;

OutputParamsStorage output_params_storage;
int32_t reg_bias;
int32_t reg_multiplier;

int32_t reg_output_offset;
int32_t reg_output_max;
int32_t reg_output_min;

uint32_t reg_verify;
uint32_t ping_storage;
};  // namespace soft_cfu
