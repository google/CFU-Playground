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

// Tests multiply-add CFU
void do_test_cfu(void) {
  printf("\r\nCFU Test... ");

  // Calculated on a spreadsheet
  cfu_reset();
  cfu_accumulate(0x884CF61A, 0xE49F2F1C);
  cfu_accumulate(0x0BE31854, 0x527FDBCF);
  cfu_accumulate(0xADB43251, 0x4E36D172);
  cfu_accumulate(0x6F867FFB, 0x442C7B76);
  printf("%s\n", static_cast<int32_t>(cfu_read()) == 81978 ? "PASS!" : "FAIL");
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