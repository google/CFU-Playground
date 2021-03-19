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

#ifndef _MNV2_CFU_H
#define _MNV2_CFU_H

#include "cfu.h"

#ifdef __cplusplus
extern "C" {
#endif

// Defines CFU instructions used in mnv2_first
// Keep this in sync with gateware and software_cfu.c

#define CFU_GET(reg) cfu_op0(reg, 0, 0)
#define CFU_SET(reg, in0) cfu_op0(reg, in0, 0)

#define CFU_SET_INPUT_DEPTH_WORDS(in0) CFU_SET(10, in0)
#define CFU_SET_OUTPUT_DEPTH(in0) CFU_SET(11, in0)
#define CFU_SET_INPUT_OFFSET(in0) CFU_SET(12, in0)
#define CFU_SET_OUTPUT_OFFSET(in0) CFU_SET(13, in0)
#define CFU_SET_ACTIVATION_MIN(in0) CFU_SET(14, in0)
#define CFU_SET_ACTIVATION_MAX(in0) CFU_SET(15, in0)

#define CFU_SET_OUTPUT_BATCH_SIZE(in0) CFU_SET(20, in0)
#define CFU_STORE_OUTPUT_MULTIPLIER(in0) CFU_SET(21, in0)
#define CFU_STORE_OUTPUT_SHIFT(in0) CFU_SET(22, in0)
#define CFU_STORE_OUTPUT_BIAS(in0) CFU_SET(23, in0)
#define CFU_STORE_FILTER_VALUE(in0) CFU_SET(24, in0)
#define CFU_STORE_INPUT_VALUE(in0) CFU_SET(25, in0)

#define CFU_MACC4_EXPLICIT(input_vals, filter_vals) cfu_op0(30, input_vals, filter_vals)
#define CFU_MACC4_IMPLICIT() CFU_GET(31)

// Supports incremental development
#define CFU_GET_FILTER_VALUE() CFU_GET(110)
#define CFU_GET_INPUT_VALUE() CFU_GET(111)
#define CFU_MARK_INPUT_READ_FINISHED() CFU_GET(112)
#define CFU_DUMP_INPUT_STORE() CFU_GET(113)
#define CFU_POST_PROCESS(in0) CFU_SET(120, in0)

#define EBRAM_DEPTH_BITS (16*1024)
#define EBRAM_DEPTH_BYTES (EBRAM_DEPTH_BITS/8)
#define EBRAM_DEPTH_WORDS (EBRAM_DEPTH_BYTES/4)

#define NUM_FILTER_DATA_EBRAMS 4
#define NUM_FILTER_DATA_BYTES (NUM_FILTER_DATA_EBRAMS*EBRAM_DEPTH_BYTES)
#define NUM_FILTER_DATA_WORDS (NUM_FILTER_DATA_BYTES / 4)

#define NUM_INPUT_DATA_EBRAMS 4
#define NUM_INPUT_DATA_BYTES (NUM_INPUT_DATA_EBRAMS*EBRAM_DEPTH_BYTES)
#define NUM_INPUT_DATA_WORDS (NUM_INPUT_DATA_BYTES / 4)
#define MAX_CONV_INPUT_BYTES (NUM_INPUT_DATA_BYTES / 2)
#define MAX_CONV_INPUT_WORDS (MAX_CONV_INPUT_BYTES / 4)



// Useful to slow down output when it is overflowing UART buffers
static inline void delay() {
  for (int i = 0; i < 10000; i++) {
    // nop
    __asm__ __volatile__("add zero, zero, zero");
  }
}

#ifdef __cplusplus
}
#endif
#endif  // _MNV2_CFU_H