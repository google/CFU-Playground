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

#include "models/mnv2/mnv2.h"

#include <stdio.h>

#include "menu.h"
#include "metrics.h"
#include "models/mnv2/input_00001_18027.h"
#include "models/mnv2/input_00001_7281.h"
#include "models/mnv2/input_00001_7425.h"
#include "models/mnv2/input_00002_2532.h"
#include "models/mnv2/input_00002_25869.h"
#include "models/mnv2/input_00004_970.h"
#include "models/mnv2/model_mobilenetv2_160_035.h"
#include "tflite.h"

#define NUM_GOLDEN 5
struct golden_test {
  const unsigned char* data;
  int32_t expected;
};

struct golden_test golden_tests[] = {
    {input_00001_7281, -106}, {input_00001_7425, 66}, {input_00002_2532, -106},
    {input_00002_25869, 144}, {input_00004_970, 110},
};
// Initialize everything once
// deallocate tensors when done
static void mnv2_init(void) {
  tflite_load_model(model_mobilenetv2_160_035, model_mobilenetv2_160_035_len);
}

// Run classification, after input has been loaded
static int32_t mnv2_classify() {
  printf("Running mnv2\n");
  DCACHE_SETUP_METRICS;
  tflite_classify();
  DCACHE_PRINT_METRICS;

  // Process the inference results.
  int8_t* output = tflite_get_output();
  return (int32_t)output[1] - (int32_t)output[0];
}

static void do_classify_zeros() {
  tflite_set_input_zeros();
  int32_t result = mnv2_classify();
  printf("Result is %ld\n", result);
}

static void do_classify_0() {
  tflite_set_input_unsigned(golden_tests[0].data);
  int32_t result = mnv2_classify();
  printf("Result is %ld\n", result);
}

static void do_classify_1() {
  tflite_set_input_unsigned(golden_tests[1].data);
  int32_t result = mnv2_classify();
  printf("Result is %ld\n", result);
}

static void do_classify_special() {
  tflite_set_input_unsigned(input_00001_18027);
  int32_t result = mnv2_classify();
  printf("Result is %ld\n", result);
}

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; i < NUM_GOLDEN; i++) {
    tflite_set_input_unsigned(golden_tests[i].data);
    int actual = mnv2_classify();
    int expected = golden_tests[i].expected;
    if (actual != expected) {
      failed = true;
      printf("*** Golden test %d failed: %d (actual) != %d (expected))\n", i,
             actual, expected);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}
static struct Menu MENU = {
    "Tests for mnv2 model",
    "mnv2",
    {
        MENU_ITEM('0', "Run test 0", do_classify_0),
        MENU_ITEM('1', "Run test 1", do_classify_1),
        MENU_ITEM('s', "Run special test", do_classify_special),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_ITEM('z', "Run with zeros input", do_classify_zeros),
        MENU_END,
    },
};

// For integration into menu system
void mnv2_menu() {
  mnv2_init();
  menu_run(&MENU);
}
