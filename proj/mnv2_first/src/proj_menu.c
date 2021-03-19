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

#include "proj_menu.h"

#include <stdio.h>
#include <string.h>

#include "b64_util.h"
#include "cfu.h"
#include "cpp_math.h"
#include "generated/csr.h"
#include "golden_op_tests.h"
#include "menu.h"

static void print_sample(char* s) {
  printf("in = %s\n", s);
  b64_dump(s, strlen(s));
}

static void do_b64_samples() {
  print_sample("1234");
  // See https://en.wikipedia.org/wiki/Base64#Examples
  print_sample(
      "Man is distinguished, not only by his reason, but by this singular "
      "passion from other animals, which is a lust of the mind, that by a "
      "perseverance of delight in the continued and indefatigable generation "
      "of knowledge, exceeds the short vehemence of any carnal pleasure.");
}

// See
// https://en.wikipedia.org/wiki/Linear_congruential_generator#Parameters_in_common_use
const int64_t rand_a = 6364136223846793005;
const int64_t rand_c = 1442695040888963407;
int32_t next_random(int64_t* r) {
  *r = (*r) * rand_a + rand_c;
  // Use higher order bits
  return *r >> 28;
}

static void do_srdhm_tests() {
  int64_t r = 0x0;
  for (int i = 0; i < 1024; i++) {
    int32_t a = next_random(&r);
    int32_t b = next_random(&r);

    // sim_trace_enable_write(1);

    int32_t sw = cpp_math_srdhm_software(a, b);
    int32_t gw = cfu_op7_hw(0, a, b);

    if (gw != sw || (i % 128 == 0)) {
      printf("srdhm(0x%08lx, 0x%08lx) = ", a, b);
      printf("0x%08lx", sw);
      if (gw != sw) {
        printf("   gw = 0x%08lx", gw);
      }
      printf("\n");
    }
  }
}

static void do_mbqm_tests() {
  int64_t r = 0x0;
  for (int i = 0; i < 1024 * 64; i++) {
    int32_t x = next_random(&r);
    int32_t quantized_multiplier = next_random(&r);
    int shift = next_random(&r) & 0x1f;
    if (next_random(&r) & 1) {
      shift = -shift;
    }

    int32_t sw =
        cpp_math_mul_by_quantized_mul_software(x, quantized_multiplier, shift);
    int32_t gw1 =
        cpp_math_mul_by_quantized_mul_gateware1(x, quantized_multiplier, shift);
    int32_t gw2 =
        cpp_math_mul_by_quantized_mul_gateware2(x, quantized_multiplier, shift);
    if (gw1 != sw || gw2 != sw || (i % (1024 * 8) == 0)) {
      printf("mbqm(0x%08lx, 0x%08lx, %3d) = ", x, quantized_multiplier, shift);
      printf("0x%08lx", sw);
      if (gw1 != sw || gw2 != sw) {
        printf("   gw1 = 0x%08lx, gw2 = 0x%08lx", gw1, gw2);
      }
      printf("\n");
    }
  }
}

static void do_rdbpot_tests() {
  int64_t r = 0x1234;
  for (int i = 0; i < 1024; i++) {
    int32_t x = next_random(&r);
    int exponent = next_random(&r) & 0x1f;
    int32_t sw = cpp_math_rdbpot_software(x, exponent);
    int32_t gw = cfu_op6_hw(0, x, exponent);
    if (gw != sw || (i % 128 == 0)) {
      printf("rdbpot(0x%08lx, %3d) = ", x, exponent);
      printf("0x%08lx", sw);
      if (gw != sw) {
        printf("   gw = 0x%08lx", gw);
      }
      printf("\n");
    }
  }
}

static void do_explicit_macc4_tests() {
  int failcount = 0;

  // sim_trace_enable_write(1);
  int64_t r = 0x0;
  for (int i = 0; i < 1024; i++) {
    int32_t in_val = next_random(&r);
    int32_t f_val = next_random(&r);
    int32_t offset = next_random(&r);
    if (offset & 0x100) {
      offset = 0x80;
    } else {
      offset = (int8_t)offset;
    }

    cfu_op0_sw(12, offset, 0);
    cfu_op0_hw(12, offset, 0);
    int32_t sw = cfu_op0_sw(30, in_val, f_val);
    int32_t hw = cfu_op0_hw(30, in_val, f_val);

    if (hw != sw) {
      printf("off=%08lx in=%08lx filt=%08lx -->sw=%08lx, hw=%08lx\n", offset,
             in_val, f_val, sw, hw);
      failcount++;
    }
  }
  if (!failcount) {
    printf("All OK\n");
  }
}

#ifdef PLATFORM_sim
static void do_start_trace() {
  printf("Start trace\n");
  sim_trace_enable_write(1);
}

static void do_quit_sim() {
  printf("BYE\n");
  sim_finish_finish_write(1);
}
#endif

static struct Menu MENU = {
    "Project Menu",
    "mnv2_first",
    {
        MENU_ITEM('1', "1x1 conv2d golden tests", golden_op_run_1x1conv),
        MENU_ITEM('2', "base64 samples", do_b64_samples),
        MENU_ITEM('3', "srdhm tests", do_srdhm_tests),
        MENU_ITEM('4', "rdbpot tests", do_rdbpot_tests),
        MENU_ITEM('5', "mbqm tests", do_mbqm_tests),
        MENU_ITEM('6', "explicit macc 4", do_explicit_macc4_tests),
#ifdef PLATFORM_sim
        MENU_ITEM('t', "Trace sim", do_start_trace),
        MENU_ITEM('Q', "Quit sim", do_quit_sim),
#endif
        MENU_END,
    },
};

void do_proj_menu() {
  // sim_trace_enable_write(1);
  menu_run(&MENU);
}