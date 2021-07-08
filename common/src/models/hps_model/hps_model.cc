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
#include "models/hps_model/hps_model_2021_07_05.h"
#include "tflite.h"

namespace {

// Initialize everything once
// deallocate tensors when done
void init(void) {
  tflite_load_model(hps_model_2021_07_05, hps_model_2021_07_05_len);
}

// Run classification, after input has been loaded
int32_t classify(const char* desc) {
  printf("Running %s\n", desc);
  tflite_classify();

  // Process the inference results.
  int8_t* output = tflite_get_output();
  return (int32_t)output[1] - (int32_t)output[0];
}

// Classify with random data
int32_t classify_random_1() {
  constexpr int64_t INPUT_SEED_1 = 0x1234567890abcdef;
  tflite_randomize_input(INPUT_SEED_1);
  return classify("random 1");
}

void do_classify_random_1() { printf("Result is %ld\n", classify_random_1()); }

// Classify with a grid pattern
int32_t classify_grid() {
  tflite_set_grid_input();
  return classify("grid");
}

void do_classify_grid() { printf("Result is %ld\n", classify_grid()); }

// Set input to zero and run classification
int32_t classify_zeros() {
  tflite_set_input_zeros();
  return classify("zeroed input");
}

void do_classify_zeros() { printf("Result is %ld\n", classify_zeros()); }

// Golden tests: expected results
struct GoldenTest {
  int32_t (*fn)();
  int32_t expected;
};

GoldenTest golden_tests[4] = {
    {classify_random_1, 0},
    {classify_grid, -3},
    {classify_zeros, -1},
    {nullptr, 0},
};

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; golden_tests[i].fn; i++) {
    int32_t actual = golden_tests[i].fn();
    int32_t expected = golden_tests[i].expected;
    if (actual != expected) {
      failed = true;
      printf("*** Golden test %d failed: %ld (actual) != %ld (expected))\n", i,
             actual, expected);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

struct Menu MENU = {
    "Tests for HPS model model",
    "hps",
    {
        MENU_ITEM('1', "Run with random input seed #1", do_classify_random_1),
        MENU_ITEM('2', "Run with grid", do_classify_grid),
        MENU_ITEM('z', "Run with zeros input", do_classify_zeros),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

}  // anonymous namespace

// For integration into menu system
extern "C" void hps_model_menu() {
  init();
  menu_run(&MENU);
}
