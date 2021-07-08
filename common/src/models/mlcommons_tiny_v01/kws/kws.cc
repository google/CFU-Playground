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

#include "models/mlcommons_tiny_v01/kws/kws.h"

#include <stdio.h>

#include "menu.h"
#include "metrics.h"
#include "models/mlcommons_tiny_v01/kws/test_data/down_0.h"
#include "models/mlcommons_tiny_v01/kws/test_data/go_1.h"
#include "models/mlcommons_tiny_v01/kws/test_data/left_2.h"
#include "models/mlcommons_tiny_v01/kws/test_data/no_3.h"
#include "models/mlcommons_tiny_v01/kws/test_data/off_4.h"
#include "models/mlcommons_tiny_v01/kws/test_data/on_5.h"
#include "models/mlcommons_tiny_v01/kws/test_data/right_6.h"
#include "models/mlcommons_tiny_v01/kws/test_data/silence_10.h"
#include "models/mlcommons_tiny_v01/kws/test_data/stop_7.h"
#include "models/mlcommons_tiny_v01/kws/test_data/unkown_11.h"
#include "models/mlcommons_tiny_v01/kws/test_data/up_8.h"
#include "models/mlcommons_tiny_v01/kws/test_data/yes_9.h"
#include "tflite.h"
#include "tiny/v0.1/training/keyword_spotting/trained_models/kws_ref_model.h"

// The kws model classifies speech based on the greatest of 12 scores.
typedef struct {
  int8_t down_score;
  int8_t go_score;
  int8_t left_score;
  int8_t no_score;
  int8_t off_score;
  int8_t on_score;
  int8_t right_score;
  int8_t stop_score;
  int8_t up_score;
  int8_t yes_score;
  int8_t silence_score;
  int8_t unknown_score;
} V01KeywordSpottingResult;

#define NUM_GOLDEN 12

// Inputs and expected outputs for all test cases.
struct {
  const unsigned char* data;
  V01KeywordSpottingResult actual;
} mlcommons_tiny_v01_kws_dataset[NUM_GOLDEN] = {
    {down_0,
     {127, -128, -128, -128, -128, -128, -128, -128, -128, -128, -128, -128}},
    {go_1,
     {-128, 127, -128, -127, -128, -128, -128, -128, -128, -128, -128, -128}},
    {left_2,
     {-128, -128, 126, -128, -128, -128, -128, -128, -128, -128, -128, -126}},
    {no_3,
     {-127, -29, -128, 25, -128, -128, -128, -128, -128, -128, -128, -125}},
    {off_4,
     {-128, -128, -128, -128, 127, -128, -128, -128, -128, -128, -128, -128}},
    {on_5,
     {-128, -128, -128, -128, -128, 127, -128, -128, -128, -128, -128, -128}},
    {right_6,
     {-128, -128, -128, -128, -128, -128, 127, -128, -128, -128, -128, -128}},
    {stop_7,
     {-128, -128, -128, -128, -128, -128, -128, 127, -128, -128, -128, -128}},
    {up_8,
     {-128, -128, -128, -128, -127, -128, -128, -128, 127, -128, -128, -128}},
    {yes_9,
     {-128, -128, -128, -128, -128, -128, -128, -128, -128, 127, -128, -128}},
    {silence_10,
     {-128, -128, -128, -128, -128, -128, -128, -128, -128, -128, 127, -127}},
    {unkown_11,
     {-128, -128, -128, -128, -128, -128, -128, -128, -128, -128, -128, 127}},
};

static void kws_init(void) {
  tflite_load_model(kws_ref_model, kws_ref_model_len);
}

V01KeywordSpottingResult kws_classify() {
  printf("Running kws\n");
  DCACHE_SETUP_METRICS;
  tflite_classify();
  DCACHE_PRINT_METRICS;

  int8_t* output = tflite_get_output();
  return (V01KeywordSpottingResult){
      output[0], output[1], output[2], output[3], output[4],  output[5],
      output[6], output[7], output[8], output[9], output[10], output[11],
  };
}

static void print_keyword_spotting_result(const char* prefix,
                                          V01KeywordSpottingResult res) {
  printf(
      "%s-- down: %d, go: %d, left: %d, no: %d, off: %d, on: %d, right: "
      "%d, stop: %d, up: %d, yes: %d, silence: %d, unkown: %d\n",
      prefix, res.down_score, res.go_score, res.left_score, res.no_score,
      res.off_score, res.on_score, res.right_score, res.stop_score,
      res.up_score, res.yes_score, res.silence_score, res.unknown_score);
}

#define MLCOMMONS_TINY_V01_KWS_TEST(name, test_index)                  \
  static void name() {                                                 \
    puts(#name);                                                       \
    tflite_set_input(mlcommons_tiny_v01_kws_dataset[test_index].data); \
    print_keyword_spotting_result("  result", kws_classify());         \
  }

// Smattering of tests for the menu, more can be easily added/removed.

MLCOMMONS_TINY_V01_KWS_TEST(do_classify_down, 0);
MLCOMMONS_TINY_V01_KWS_TEST(do_classify_go, 1);
MLCOMMONS_TINY_V01_KWS_TEST(do_classify_left, 2);

#undef MLCOMMONS_TINY_V01_KWS_TEST

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; i < NUM_GOLDEN; i++) {
    tflite_set_input(mlcommons_tiny_v01_kws_dataset[i].data);
    V01KeywordSpottingResult res = kws_classify();
    V01KeywordSpottingResult exp = mlcommons_tiny_v01_kws_dataset[i].actual;
    if (res.down_score != exp.down_score || res.go_score != exp.go_score ||
        res.left_score != exp.left_score || res.no_score != exp.no_score ||
        res.off_score != exp.off_score || res.on_score != exp.on_score ||
        res.right_score != exp.right_score ||
        res.stop_score != exp.stop_score || res.up_score != exp.up_score ||
        res.yes_score != exp.yes_score ||
        res.silence_score != exp.silence_score ||
        res.unknown_score != exp.unknown_score) {
      failed = true;
      printf("*** Golden test %d failed: \n", i);
      print_keyword_spotting_result("actual", res);
      print_keyword_spotting_result("expected", exp);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

static struct Menu MENU = {
    "Tests for kws model",
    "kws",
    {
        MENU_ITEM('0', "Run with \"down\" input", do_classify_down),
        MENU_ITEM('1', "Run with \"go\" input", do_classify_go),
        MENU_ITEM('2', "Run with \"left\" input", do_classify_left),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void mlcommons_tiny_v01_kws_menu() {
  kws_init();
  menu_run(&MENU);
}
