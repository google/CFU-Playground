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

namespace {

// Template Fn
void do_hello_world(void) { puts("Hello, World!!!\n"); }

// Test template instruction
void do_exercise_cfu_op0(void) {
  puts("\r\nExercise CFU Op0 aka ADD\r\n");

  unsigned int a = 0;
  unsigned int b = 0;
  unsigned int cfu = 0;
  unsigned int count = 0;
  unsigned int pass_count = 0;
  unsigned int fail_count = 0;

  for (a = 0x00004567; a < 0xF8000000; a += 0x00212345) {
    for (b = 0x0000ba98; b < 0xFF000000; b += 0x00770077) {
      cfu = cfu_op0(0, a, b);
      if (cfu != a + b) {
        printf("[%4d] a: %08x b:%08x a+b=%08x cfu=%08x FAIL\r\n", count, a, b,
               a + b, cfu);
        fail_count++;
      } else {
        pass_count++;
      }
      count++;
    }
  }

  printf("\r\nPerformed %d comparisons, %d pass, %d fail\r\n", count,
         pass_count, fail_count);
}

struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('0', "exercise cfu op0", do_exercise_cfu_op0),
        MENU_ITEM('h', "say Hello", do_hello_world),
        MENU_END,
    },
};
};  // anonymous namespace

extern "C" void do_proj_menu() { menu_run(&MENU); }
