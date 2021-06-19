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

// Dumps data for processing outside
#ifndef _DUMP_H
#define _DUMP_H

#include <stdint.h>
#include <stddef.h>

// Dump len bytes of data
void dump_hex(const uint8_t* data, size_t len);

// Dump len words of data
void dump_hex(const int32_t* data, size_t len);

#endif  // _DUMP_H
