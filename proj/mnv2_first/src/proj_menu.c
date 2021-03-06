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
  for (int i = 0; i < 1024*128; i++) {
    int32_t x = next_random(&r);
    int32_t quantized_multiplier = next_random(&r);
    int shift = next_random(&r) & 0x3f;
    if (shift > 31) {
      shift = 31 - shift;
    }

    int32_t sw =
        cpp_math_mul_by_quantized_mul_software(x, quantized_multiplier, shift);
    int32_t gw =
        cpp_math_mul_by_quantized_mul_gateware1(x, quantized_multiplier, shift);
    if (gw != sw || (i % 128 == 0)) {
      printf("mbqm(0x%08lx, 0x%08lx, %3d) = ", x, quantized_multiplier, shift);
      printf("0x%08lx", sw);
      if (gw != sw) {
        printf("   gw = 0x%08lx", gw);
      }
      printf("\n");
    }
  }
}

static struct Menu MENU = {
    "Project Menu",
    "mnv2_first",
    {
        MENU_ITEM('1', "1x1 conv2d golden tests", golden_op_run_1x1conv),
        MENU_ITEM('2', "base64 samples", do_b64_samples),
        MENU_ITEM('3', "srdhm tests", do_srdhm_tests),
        MENU_ITEM('4', "mbqm tests", do_mbqm_tests),
        MENU_END,
    },
};

void do_proj_menu() { menu_run(&MENU); }