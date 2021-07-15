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

#include "models/mlcommons_tiny_v01/vww/vww.h"

#include <stdio.h>

#include "menu.h"
#include "metrics.h"
#include "models/mlcommons_tiny_v01/vww/test_data/quant_test_no_0.h"
#include "models/mlcommons_tiny_v01/vww/test_data/quant_test_no_1.h"
#include "models/mlcommons_tiny_v01/vww/test_data/quant_test_yes_0.h"
#include "models/mlcommons_tiny_v01/vww/test_data/quant_test_yes_1.h"
#include "tflite.h"
#include "tiny/v0.1/training/visual_wake_words/trained_models/vww_96_int8.h"

#define NUM_GOLDEN 4

struct {
  const unsigned char* data;
  int32_t actual;
} mlcommons_tiny_v01_vww_dataset[NUM_GOLDEN] = {
    {quant_test_no_0, -238},
    {quant_test_no_1, -150},
    {quant_test_yes_0, 120},
    {quant_test_yes_1, 146},
};

static void vww_init(void) { tflite_load_model(vww_96_int8, vww_96_int8_len); }

int32_t vww_classify() {
  printf("Running vww\n");
  PERF_SETUP_METRICS;
  tflite_classify();
  PERF_PRINT_METRICS;

  int8_t* output = tflite_get_output();
  return (int32_t)output[1] - output[0];
}

#define MLCOMMONS_TINY_V01_VWW_TEST(name, test_index)                  \
  static void name() {                                                 \
    puts(#name);                                                       \
    tflite_set_input(mlcommons_tiny_v01_vww_dataset[test_index].data); \
    printf("  result-- score: %ld\n", vww_classify());                 \
  }

MLCOMMONS_TINY_V01_VWW_TEST(do_classify_no_person, 0);
MLCOMMONS_TINY_V01_VWW_TEST(do_classify_person, 2);

#undef MLCOMMONS_TINY_V01_VWW_TEST

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; i < NUM_GOLDEN; i++) {
    tflite_set_input(mlcommons_tiny_v01_vww_dataset[i].data);
    int32_t res = vww_classify();
    int32_t exp = mlcommons_tiny_v01_vww_dataset[i].actual;
    if (res != exp) {
      failed = true;
      printf("*** Golden test %d failed: \n", i);
      printf("actual-- score: %ld\n", res);
      printf("expected-- score: %ld\n", exp);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

static struct Menu MENU = {
    "Tests for vww model",
    "vww",
    {
        MENU_ITEM('0', "Run with no person input", do_classify_no_person),
        MENU_ITEM('1', "Run with person input", do_classify_person),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void mlcommons_tiny_v01_vww_menu() {
  vww_init();
  menu_run(&MENU);
}
