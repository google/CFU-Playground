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

#include <stdio.h>

#include "menu.h"
#include "models/hps_model/cat_picture.h"
#include "models/hps_model/diagram.h"
#include "models/hps_model/hps_model_2021_07_05_tiled.h"
#include "models/hps_model/hps_model_2021_07_05_untiled.h"
#include "tflite.h"

namespace {

// Initialize with the tiled version
void init_tiled(void) {
  puts("Loading Tiled HPS model");
  tflite_load_model(hps_model_2021_07_05_tiled, hps_model_2021_07_05_tiled_len);
}

// Initialize with the untiled version
void init_untiled(void) {
  puts("Loading Untiled HPS model");
  tflite_load_model(hps_model_2021_07_05_untiled, hps_model_2021_07_05_untiled_len);
}

// Run classification and interpret results
int32_t classify() {
  tflite_classify();
  int8_t* output = tflite_get_output();
  return output[0];
}

// Classify with random data
int32_t classify_cat() {
  tflite_set_input_unsigned(cat_picture);
  return classify();
}

void do_classify_cat() { printf("Result is %ld\n", classify_cat()); }

// Classify with a grid pattern
int32_t classify_diagram() {
  tflite_set_input_unsigned(diagram);
  return classify();
}

void do_classify_diagram() { printf("Result is %ld\n", classify_diagram()); }

// Set input to zero and run classification
int32_t classify_zeros() {
  tflite_set_input_zeros();
  return classify();
}

void do_classify_zeros() { printf("Result is %ld\n", classify_zeros()); }

// Golden tests: expected results
struct GoldenTest {
  int32_t (*fn)();
  const char* name;
  int32_t expected;
};

GoldenTest golden_tests[4] = {
    {classify_cat, "cat", -116},
    {classify_diagram, "diagram", -124},
    {classify_zeros, "zeroes", -123},
    {nullptr, "", 0},
};

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; golden_tests[i].fn; i++) {
    printf("Testing input %s: ", golden_tests[i].name);
    int32_t actual = golden_tests[i].fn();
    int32_t expected = golden_tests[i].expected;
    if (actual != expected) {
      failed = true;
      printf("FAIL %ld (actual) != %ld (expected) ***\n", actual, expected);
    } else {
      printf("OK\n");
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

struct Menu MENU = {
    "Tests for HPS model",
    "hps",
    {
        MENU_ITEM('t', "reinitialize with Tiled model", init_tiled),
        MENU_ITEM('u', "reinitialize with Untiled model", init_untiled),
        MENU_ITEM('c', "Cat picture input", do_classify_cat),
        MENU_ITEM('d', "Diagram input", do_classify_diagram),
        MENU_ITEM('z', "Zeros input", do_classify_zeros),
        MENU_ITEM('g', "Golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

}  // anonymous namespace

// For integration into menu system
extern "C" void hps_model_menu() {
  init_tiled();
  menu_run(&MENU);
}
