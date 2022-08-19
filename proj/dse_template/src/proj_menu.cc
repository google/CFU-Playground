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
#include "golden_op_tests.h"
#include "menu.h"

namespace {
void print_sample(const char* s) {
  printf("in = %s\n", s);
  b64_dump(static_cast<const int8_t*>(static_cast<const void*>(s)), strlen(s));
}

void do_b64_samples() {
  print_sample("1234");
  // See https://en.wikipedia.org/wiki/Base64#Examples
  print_sample(
      "Man is distinguished, not only by his reason, but by this singular "
      "passion from other animals, which is a lust of the mind, that by a "
      "perseverance of delight in the continued and indefatigable generation "
      "of knowledge, exceeds the short vehemence of any carnal pleasure.");
}

struct Menu MENU = {
    "Project Menu",
    "mnv2_first",
    {
        MENU_ITEM('1', "1x1 conv2d golden tests", golden_op_run_1x1conv),
        MENU_ITEM('2', "base64 samples", do_b64_samples),
        MENU_END,
    },
};
};  // anonymous namespace

extern "C" void do_proj_menu() {
  // sim_trace_enable_write(1);
  menu_run(&MENU);
}