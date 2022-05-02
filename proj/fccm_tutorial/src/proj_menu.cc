/*
 * Copyright 2022 The CFU-Playground Authors
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

#include "fccm_cfu.h"
#include "menu.h"

namespace {

// Template Fn
void do_hello_world(void) { puts("Hello, World!!!\n"); }

void check_cfu(uint32_t a, uint32_t b, uint32_t expected) {
  cfu_accumulate(a, b);
  uint32_t actual = cfu_read();
  printf("%08lx ", actual);
  if (actual == expected) {
    printf("ok\n");
  } else {
    printf("FAIL (0x%08lx) %ld != %ld\n", expected, actual, expected);
  }
}

// Tests multiply-add CFU
void do_test_cfu(void) {
  printf("\r\nCFU Test... ");

  cfu_reset();
  printf("%08lx\n", cfu_read());

  check_cfu(0x00808080, 0x98000000, -13312);
  check_cfu(0x80B38080, 0x002B0000, -11119);
  check_cfu(0x8080E180, 0x0000AE00, -19073);
  check_cfu(0x8080801C, 0x000000AD, -32021);
}

struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('1', "test cfu", do_test_cfu),
        MENU_ITEM('h', "say Hello", do_hello_world),
        MENU_END,
    },
};
};  // anonymous namespace

extern "C" void do_proj_menu() { menu_run(&MENU); }