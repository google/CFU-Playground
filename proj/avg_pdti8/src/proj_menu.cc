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

#include "cfu.h"
#include "menu.h"
#include "pdti8_math.h"

namespace {

// Template Fn
void do_hello_world(void) { puts("Hello, World!!!\n"); }

// Test template instruction
void do_srdhm(void) {
  puts("\nTest SaturatingRoundingDoublingHighMul");
  // sim_trace_enable_write(1);
  int trials = 0;
  int mismatches = 0;
  for (int32_t a = -0x71234567; a < 0x68000000; a += 0x10012345) {
    for (int32_t b = -0x7edcba98; b < 0x68000000; b += 0x10770077) {
      trials++;
      int32_t gem = math_srdhm_gemmlowp(a, b);
      int32_t cfu = math_srdhm_cfu(a, b);
      if (gem != cfu) {
        mismatches++;
        printf("mismatch: srdhm(%10ld, %10ld) = %10ld, %10ld\n", a, b, gem,
               cfu);
      }
    }
  }
  printf("Performed %d comparisons, %d failures", trials, mismatches);
}

// Test template instruction
void do_rdbypot(void) {
  puts("\nTest RoundingDivideByPOT");
  // sim_trace_enable_write(1);
  int trials = 0;
  int mismatches = 0;
  for (int32_t x = -0x71234567; x < 0x68000000; x += 0x10012345) {
    for (int exponent = -5; exponent >= -10; exponent--) {
      trials++;
      int32_t gem = math_rdbypot_gemmlowp(x, exponent);
      int32_t cfu = math_rdbypot_cfu(x, exponent);
      if (gem != cfu) {
        mismatches++;
        printf("mismatch: srdhm(%10ld, %d) = %10ld, %10ld\n", x, exponent, gem,
               cfu);
      }
    }
  }
  printf("Performed %d comparisons, %d failures", trials, mismatches);
}

struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('0', "SaturatingRoundingDoublingHighMul - local impl vs lib",
                  do_srdhm),
        MENU_ITEM('1', "RoundingDivideByPOT - local impl vs lib", do_rdbypot),
        MENU_ITEM('h', "say Hello", do_hello_world),
        MENU_END,
    },
};

};  // anonymous namespace

extern "C" void do_proj_menu() { menu_run(&MENU); }
