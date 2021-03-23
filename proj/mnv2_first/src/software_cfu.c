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

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "cfu.h"
#include "cpp_math.h"
#include "mnv2_cfu.h"

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

// Filter store
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

// Input store is double buffered: reading and writing occur on different
// bufers.
struct InputStore {
  // There are two buffers, 0 and 1.

  // Write allowed is set by the reader to indicate buffer is now empty.
  // It is cleared by the reader when the reader begins processing that buffer.
  bool write_allowed[2];

  // Read allowed is set by writer and inidicates the buffer is full
  // It is cleared by the writer when the writer begins processing that buffer.
  bool read_allowed[2];

  // curr_read_buffer points to the buffer that the reader will next read.
  int curr_read_buffer;

  // curr_read_buffer points to the buffer that the reader will next read.
  int curr_write_buffer;

  // Actual data storage
  int32_t values[NUM_INPUT_DATA_EBRAMS][NUM_INPUT_DATA_WORDS];

  // Input depth in 32 bit (4 byte) words
  uint32_t input_depth;

  // Address at which to next write and read in current read buffer, in 32 bit
  // words.
  uint32_t write_addr;
  uint32_t read_addr;
};

static struct InputStore input_store;

static void input_store_restart(struct InputStore* is) {
  memset(is, 0, sizeof(struct FilterStore));
  is->write_allowed[0] = true;
  is->write_allowed[1] = true;
}

static int32_t input_store_set(struct InputStore* is, uint32_t val) {
  if (!is->write_allowed[is->curr_write_buffer]) {
    // in gateware, this will be a stall
    printf("could not write\n");
    return 0;
  }

  // Not allowed to read buffer while writing
  is->read_allowed[is->curr_write_buffer] = false;

  // Calculate write address and write
  int bank = is->write_addr & 0x3;
  int w_addr = (is->write_addr >> 2) +
               (is->curr_write_buffer ? EBRAM_DEPTH_WORDS / 2 : 0);
  is->values[bank][w_addr] = val;
  // printf("is->values[%d][%d] = %08lx\n", bank, w_addr, val);

  // End of batch: reset address, mark buffer full and readable and go to next
  // buffer
  is->write_addr++;
  if (is->write_addr == is->input_depth) {
    is->write_addr = 0;
    is->read_allowed[is->curr_write_buffer] = true;
    is->curr_write_buffer = 1 - is->curr_write_buffer;
  }
}

// Eventually, reads will all be 4 words (16 bytes) wide
static uint32_t input_store_read(struct InputStore* is) {
  if (!is->read_allowed[is->curr_read_buffer]) {
    // in gateware, this will be a stall
    printf("could not read\n");
    return 0;
  }

  // Not allowed to write buffer while reading
  is->write_allowed[is->curr_read_buffer] = false;

  // Calculate read address and read
  int bank = is->read_addr & 0x3;
  int r_addr =
      (is->read_addr >> 2) + (is->curr_read_buffer ? EBRAM_DEPTH_WORDS / 2 : 0);
  uint32_t result = is->values[bank][r_addr];

  // End of input: reset address, mark buffer empy and writeable and go to next
  // buffer
  is->read_addr++;
  if (is->read_addr == is->input_depth) {
    is->read_addr = 0;
  }

  return result;
}

static uint32_t input_store_mark_read_finished(struct InputStore* is) {
  // reset address, mark buffer empy and writeable and go to next buffer
  is->read_addr = 0;
  is->write_allowed[is->curr_read_buffer] = true;
  is->curr_read_buffer = 1 - is->curr_read_buffer;
  return 0;
}

static inline int32_t macc(const int8_t input_val, int8_t filter_val) {
  return ((int32_t)filter_val) * ((int32_t)input_val + reg_input_offset);
}

static int32_t macc4(uint32_t input_vals, uint32_t filter_vals) {
  int32_t result = 0;
  result += macc(input_vals & 0xff, filter_vals & 0xff);
  filter_vals >>= 8;
  input_vals >>= 8;
  result += macc(input_vals & 0xff, filter_vals & 0xff);
  filter_vals >>= 8;
  input_vals >>= 8;
  result += macc(input_vals & 0xff, filter_vals & 0xff);
  filter_vals >>= 8;
  input_vals >>= 8;
  result += macc(input_vals & 0xff, filter_vals & 0xff);
  return result;
}

static int32_t macc4_run4(struct InputStore* is, struct FilterStore* fs) {
  uint32_t result = 0;
  for (int i = 0; i < 4; i++) {
    int32_t accumulator = 0;
    for (uint32_t j = 0; j < is->input_depth; j++) {
      accumulator += macc4(input_store_read(&input_store),
                           filter_store_read(&filter_store));
    }
    result = (result >> 8) | ((0xff & post_process(accumulator)) << 24);
  }
  return result;
}

// Set register instruction
static uint32_t set_reg(int funct7, uint32_t in0, uint32_t in1) {
  switch (funct7) {
    case 10:
      input_store_restart(&input_store);
      input_store.input_depth = in0;
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

    case 20:
      // set size of output channel batch, resetting param stores
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
    case 25:
      return input_store_set(&input_store, in0);

    case 32:
      return macc4_run4(&input_store, &filter_store);

    case 112:
      return input_store_mark_read_finished(&input_store);

    default:
      return 0;
  }
  return 0;
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
