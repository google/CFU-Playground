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

#include "models/mlcommons_tiny_v01/anomd/anomd.h"

#include <stdio.h>

#include "menu.h"
#include "metrics.h"
#include "models/mlcommons_tiny_v01/anomd/test_data/quant_anomaly_0.h"
#include "models/mlcommons_tiny_v01/anomd/test_data/quant_anomaly_1.h"
#include "models/mlcommons_tiny_v01/anomd/test_data/quant_anomaly_2.h"
#include "models/mlcommons_tiny_v01/anomd/test_data/quant_normal_0.h"
#include "models/mlcommons_tiny_v01/anomd/test_data/quant_normal_1.h"
#include "models/mlcommons_tiny_v01/anomd/test_data/quant_normal_2.h"
#include "tflite.h"
#include "tiny/v0.1/training/anomaly_detection/trained_models/ad01_int8.h"

#define NUM_GOLDEN 6

struct {
  const unsigned char* data;
  uint32_t actual;
} mlcommons_tiny_v01_ad_dataset[NUM_GOLDEN] = {
    {quant_anomaly_0, 0x2268a03d}, {quant_anomaly_1, 0xefeefb35},
    {quant_anomaly_2, 0x8c908c27}, {quant_normal_0, 0xd02be5d},
    {quant_normal_1, 0x2bc9ce4a},  {quant_normal_2, 0xe7251f32},
};

static void anomd_init(void) { tflite_load_model(ad01_int8, ad01_int8_len); }

// 32 bit xor reduction used because comparing 640 outputs is unwieldy.
uint32_t uint32_xor_reduction(int8_t* output, unsigned int length) {
  uint32_t x = 0;
  int8_t j = 0;
  for (size_t i = 0; i < length; i++) {
    x ^= output[i] << ((j++ & 0x3) << 3);
  }
  return x;
}

uint32_t anomd_classify() {
  printf("Running anomd\n");
  PERF_SETUP_METRICS;
  tflite_classify();
  PERF_PRINT_METRICS;

  int8_t* output = tflite_get_output();
  return uint32_xor_reduction(output, 640);
}

#define MLCOMMONS_TINY_V01_ANOMALY_DETECTION_TEST(name, test_index)   \
  static void name() {                                                \
    puts(#name);                                                      \
    tflite_set_input(mlcommons_tiny_v01_ad_dataset[test_index].data); \
    printf("  result-- 32 bit xor: 0x%lx\n", anomd_classify());       \
  }

// Smattering of tests for the menu, more can be easily added/removed.

MLCOMMONS_TINY_V01_ANOMALY_DETECTION_TEST(do_classify_anomaly_0, 0);
MLCOMMONS_TINY_V01_ANOMALY_DETECTION_TEST(do_classify_anomaly_1, 1);
MLCOMMONS_TINY_V01_ANOMALY_DETECTION_TEST(do_classify_normal_0, 3);
MLCOMMONS_TINY_V01_ANOMALY_DETECTION_TEST(do_classify_normal_1, 4);

#undef MLCOMMONS_TINY_V01_ANOMALY_DETECTION_TEST

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; i < NUM_GOLDEN; i++) {
    tflite_set_input(mlcommons_tiny_v01_ad_dataset[i].data);
    uint32_t res = anomd_classify();
    uint32_t exp = mlcommons_tiny_v01_ad_dataset[i].actual;
    if (res != exp) {
      failed = true;
      printf("*** Golden test %d failed: \n", i);
      printf("actual: 32 bit xor: 0x%lx\n", res);
      printf("expected: 32 bit xor: 0x%lx\n", exp);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

static struct Menu MENU = {
    "Tests for anomd model",
    "anomd",
    {
        MENU_ITEM('0', "Run with anomaly 0", do_classify_anomaly_0),
        MENU_ITEM('1', "Run with normal 0", do_classify_normal_0),
        MENU_ITEM('2', "Run with anomaly 1", do_classify_anomaly_1),
        MENU_ITEM('3', "Run with normal 1", do_classify_normal_1),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void mlcommons_tiny_v01_anomd_menu() {
  anomd_init();
  menu_run(&MENU);
}
