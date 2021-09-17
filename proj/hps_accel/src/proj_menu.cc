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

#include "blocks_test.h"
#include "fixedpoint/fixedpoint.h"
#include "hps_cfu.h"
#include "menu.h"
#include "playground_util/random.h"

namespace {

#define CHECK_VALUE(actual, expected)                             \
  if (actual != expected) {                                       \
    printf("FAIL Actual %ld != Expected %d\n", actual, expected); \
    return;                                                       \
  }

void do_test_ping(void) {
  uint32_t val = cfu_ping(1, 2);
  CHECK_VALUE(val, 0);
  val = cfu_ping(12, 4);
  CHECK_VALUE(val, 3);
  val = cfu_ping(0, 0);
  CHECK_VALUE(val, 16);
  printf("OK\n");
}

void do_verify_register(void) {
  int64_t r = 0x1234567890abcdef;

  int tests = 0;
  int failures = 0;
  for (int i = 0; i < 10; i++) {
    tests += 1;
    uint32_t input = next_pseudo_random(&r);
    cfu_set(REG_VERIFY, input);
    uint32_t output = cfu_get(REG_VERIFY);
    if (output != input + 1) {
      failures += 1;
      printf("input = %08lx, output = %08lx - FAIL\n", input, output);
    }
  }
  printf("%4s: %d failures out of %d tests\n", failures ? "FAIL" : "OK",
         failures, tests);
}

struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('p', "Ping CFU", do_test_ping),
        MENU_ITEM('v', "Verify register tests", do_verify_register),
        MENU_ITEM('m', "test blocks Multiply",
                  do_test_blocks_multiply_accumulate),
        MENU_ITEM('a', "test blocks All", do_test_blocks_all),
        MENU_END,
    },
};
};  // anonymous namespace

extern "C" void do_proj_menu() { menu_run(&MENU); }
