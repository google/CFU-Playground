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
#ifndef _HPS_CFU_H
#define _HPS_CFU_H

#include "cfu.h"

// Register IDs
// For convenience, readable and writable register IDs are allocated from a
// shared pool of values 0-127.

// A write of any value to REG_RESET causes the accelerator gateware to be reset
// and lose all state
#define REG_RESET 0

// Number of input channels
#define REG_NUM_IN_CHANNELS 1

// Number of output channels
#define REG_NUM_OUT_CHANNELS 2

// Input offset for multiply-accumulate unit
#define REG_INPUT_OFFSET 3

// Set next filter word
#define REG_SET_FILTER 4

// Set next input word
#define REG_SET_INPUT 5

// These registers contain values 0-3 of the current filter word
#define REG_FILTER_0 0x10
#define REG_FILTER_1 0x11
#define REG_FILTER_2 0x12
#define REG_FILTER_3 0x13

// These registers contain values 0-3 of the current input word
#define REG_INPUT_0 0x18
#define REG_INPUT_1 0x19
#define REG_INPUT_2 0x1a
#define REG_INPUT_3 0x1b

// Set input values to multiply-accumulate unit
#define REG_MACC_IN_0 0x20
#define REG_MACC_IN_1 0x21
#define REG_MACC_IN_2 0x22
#define REG_MACC_IN_3 0x23

// Retrieve result from multiply-accumulate unit
#define REG_MACC_OUT 0x24

//  Convenience macros for get/set
#define cfu_set(reg, val) cfu_op0(reg, val, 0)
#define cfu_get(reg) cfu_op1(reg, 0, 0)

#endif  // _HPS_CFU_H