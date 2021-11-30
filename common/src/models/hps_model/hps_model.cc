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
#include "models/hps_model/hps_model_2021_09_20_tiled.h"
#include "models/hps_model/hps_second_2021_11_18_tiled.h"
#include "tflite.h"

namespace {

bool uses_09_20_model;

// Initialize models
void do_init_09_20(void) {
  puts("Loading HPS 09_20 model");
  tflite_load_model(hps_model_2021_09_20_tiled, hps_model_2021_09_20_tiled_len);
  uses_09_20_model = true;
}

void do_init_11_18(void) {
  puts("Loading HPS second 11_18 model");
  tflite_load_model(hps_second_2021_11_18_tiled, hps_second_2021_11_18_tiled_len);
  uses_09_20_model = false;
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
  int32_t expected_09_20;
  int32_t expected_11_18;
};

GoldenTest golden_tests[4] = {
    {classify_cat, "cat", -77, -126},
    {classify_diagram, "diagram", -124, -125},
    {classify_zeros, "zeroes", -126, -128},
    {nullptr, "", 0, 0},
};

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; golden_tests[i].fn; i++) {
    const GoldenTest& test = golden_tests[i];
    printf("Testing input %s: ", test.name);
    int32_t actual = test.fn();
    int32_t expected =
        uses_09_20_model ? test.expected_09_20 : test.expected_11_18;
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
        MENU_ITEM('c', "Cat picture input", do_classify_cat),
        MENU_ITEM('d', "Diagram input", do_classify_diagram),
        MENU_ITEM('z', "Zeros input", do_classify_zeros),
        MENU_ITEM('g', "Golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_ITEM('1', "Reinitialize with 09_20 model", do_init_09_20),
        MENU_ITEM('2', "Reinitialize with 11_18 model", do_init_11_18),
        MENU_END,
    },
};

}  // anonymous namespace

// For integration into menu system
extern "C" void hps_model_menu() {
  do_init_09_20();
  menu_run(&MENU);
}
