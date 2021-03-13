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

#include <stdint.h>
#include <stdio.h>

#include "cfu.h"
#include "cpp_math.h"
#include "mnv2_cfu.h"

static int32_t reg_input_depth;
static int32_t reg_output_depth;
static int32_t reg_input_offset;
static int32_t reg_output_offset;
static int32_t reg_activation_min;
static int32_t reg_activation_max;

#define MAX_OUTPUT_DEPTH 512
struct ParamStore {
  int32_t params[MAX_OUTPUT_DEPTH];
  int count;
  int read_index;
};

// These param stores store output_batch_size items
static int32_t reg_output_batch_size;
static struct ParamStore output_multiplier;
static struct ParamStore output_shift;
static struct ParamStore output_bias;

static void param_store_restart(struct ParamStore* ps) {
  ps->count = 0;
  ps->read_index = 0;
}

static int32_t param_store_set(struct ParamStore* ps, int32_t value) {
  ps->params[ps->count++] = value;
  return 0;
}

static int32_t param_store_read(struct ParamStore* ps) {
  int32_t result = ps->params[ps->read_index];
  ps->read_index += 1;
  if (ps->read_index == ps->count) {
    ps->read_index = 0;
  }
  return result;
}

static int32_t post_process(int32_t acc) {
  acc += param_store_read(&output_bias);
  acc = cpp_math_mul_by_quantized_mul_software(
      acc, param_store_read(&output_multiplier),
      param_store_read(&output_shift));
  acc += reg_output_offset;
  if (acc < reg_activation_min) {
    acc = reg_activation_min;
  } else if (acc > reg_activation_max) {
    acc = reg_activation_max;
  }
  return acc;
}

struct FilterStore {
  int32_t values[NUM_FILTER_DATA_EBRAMS][NUM_FILTER_DATA_WORDS];
  int write_index;
  int write_bank;
  int read_index;
  int read_bank;
};

static struct FilterStore filter_store;

static void filter_store_restart(struct FilterStore* fs) {
  fs->write_index = 0;
  fs->write_bank = 0;
  fs->read_index;
  fs->read_bank = 0;
}

static uint32_t filter_store_set(struct FilterStore* fs, uint32_t val) {
  fs->values[fs->write_bank][fs->write_index] = val;
  fs->write_bank = (fs->write_bank + 1) % NUM_FILTER_DATA_EBRAMS;
  if (fs->write_bank == 0) {
    fs->write_index = (fs->write_index + 1) % NUM_FILTER_DATA_WORDS;
  }
  return 0;
}

// Assumes that reads only take place after writes are complete
static uint32_t filter_store_read(struct FilterStore* fs) {
  uint32_t result = fs->values[fs->read_bank][fs->read_index];
  fs->read_bank = (fs->read_bank + 1) % NUM_FILTER_DATA_EBRAMS;
  if (fs->read_bank == 0) {
    fs->read_index = (fs->read_index + 1) % fs->write_index;
  }
  return result;
}

// Set register instruction
static uint32_t set_reg(int funct7, uint32_t in0, uint32_t in1) {
  switch (funct7) {
    case 10:
      reg_input_depth = in0;
      return 0;
    case 11:
      reg_output_depth = in0;
      return 0;
    case 12:
      reg_input_offset = in0;
      return 0;
    case 13:
      reg_output_offset = in0;
      return 0;
    case 14:
      reg_activation_min = in0;
      return 0;
    case 15:
      reg_activation_max = in0;
      break;
    case 20:  // set size of output channel batch
      reg_output_batch_size = in0;
      param_store_restart(&output_multiplier);
      param_store_restart(&output_shift);
      param_store_restart(&output_bias);
      filter_store_restart(&filter_store);
      break;
    case 21:
      return param_store_set(&output_multiplier, in0);
    case 22:
      return param_store_set(&output_shift, in0);
    case 23:
      return param_store_set(&output_bias, in0);
    case 24:
      return filter_store_set(&filter_store, in0);
      break;

    case 110:
      return filter_store_read(&filter_store);
    case 120:
      return post_process(in0);
      break;
    default:
      return 0;
  }
}

//
// In this function, place C code to emulate your CFU. You can switch between
// hardware and emulated CFU by setting the CFU_SOFTWARE_DEFINED DEFINE in
// the Makefile.
uint32_t software_cfu(int funct3, int funct7, uint32_t in0, uint32_t in1) {
  switch (funct3) {
    case 0:
      return set_reg(funct7, in0, in1);
    default:
      return 0;
  }
}
