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

#include "models/magic_wand/magic_wand.h"

#include <stdio.h>

#include "menu.h"
#include "models/magic_wand/model_magic_wand.h"
#include "tensorflow/lite/micro/examples/magic_wand/ring_micro_features_data.h"
#include "tensorflow/lite/micro/examples/magic_wand/slope_micro_features_data.h"
#include "tflite.h"

// The magic_wand model classifies based on the greatest of 4 scores.
typedef struct {
  uint32_t wing_score;
  uint32_t ring_score;
  uint32_t slope_score;
  uint32_t negative_score;
} MagicWandResult;

// Initialize everything once
// deallocate tensors when done
static void magic_wand_init(void) { tflite_load_model(model_magic_wand); }

// Run classification, after input has been loaded
MagicWandResult magic_wand_classify() {
  printf("Running magic_wand\n");
  tflite_classify();

  // Process the inference results.
  float* output = tflite_get_output_float();

  return (MagicWandResult) {
      (uint32_t) (output[0] * 1000000000),
      (uint32_t) (output[1] * 1000000000),
      (uint32_t) (output[2] * 1000000000),
      (uint32_t) (output[3] * 1000000000),
  };
}

static void do_classify_zeros() {
  tflite_set_input_zeros_float();
  MagicWandResult res = magic_wand_classify();
  printf("  results-- wing: %ld, ring: %ld, slope: %ld, negative: %ld\n",
      res.wing_score, res.ring_score, res.slope_score, res.negative_score);
}

static void do_classify_ring() {
  puts("Classify ring");
  tflite_set_input_float(g_ring_micro_f9643d42_nohash_4_data);
  MagicWandResult res = magic_wand_classify();
  printf("  results-- wing: %ld, ring: %ld, slope: %ld, negative: %ld\n",
      res.wing_score, res.ring_score, res.slope_score, res.negative_score);
}

static void do_classify_slope() {
  puts("Classify slope");
  tflite_set_input_float(g_slope_micro_f2e59fea_nohash_1_data);
  MagicWandResult res = magic_wand_classify();
  printf("  results-- wing: %ld, ring: %ld, slope: %ld, negative: %ld\n",
      res.wing_score, res.ring_score, res.slope_score, res.negative_score);
}

#define NUM_GOLDEN 3

static void do_golden_tests() {
  static MagicWandResult magic_wand_golden_results[NUM_GOLDEN] = {
      {43647280, 438047296, 86014968, 432290464},
      {39272976, 800915392, 30703206, 129108432},
      {425349, 34397, 953839872, 45700424},
  };

  MagicWandResult actual[NUM_GOLDEN];
  tflite_set_input_zeros_float();
  actual[0] = magic_wand_classify();
  tflite_set_input_float(g_ring_micro_f9643d42_nohash_4_data);
  actual[1] = magic_wand_classify();
  tflite_set_input_float(g_slope_micro_f2e59fea_nohash_1_data);
  actual[2] = magic_wand_classify();

  bool failed = false;
  for (size_t i = 0; i < NUM_GOLDEN; i++) {
    MagicWandResult res = actual[i];
    MagicWandResult exp = magic_wand_golden_results[i];
    if (res.wing_score     != exp.wing_score  ||
        res.ring_score     != exp.ring_score  ||
        res.slope_score    != exp.slope_score ||
        res.negative_score != exp.negative_score) {
      failed = true;
      printf("*** Golden test %d failed: \n", i);
      printf("actual-- wing: %ld, ring: %ld, slope: %ld, negative: %ld\n",
          res.wing_score, res.ring_score, res.slope_score, res.negative_score);
      printf("expected-- wing: %ld, ring: %ld, slope: %ld, negative: %ld\n",
          exp.wing_score, exp.ring_score, exp.slope_score, exp.negative_score);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

static struct Menu MENU = {
    "Tests for magic_wand model",
    "magic_wand",
    {
        MENU_ITEM('1', "Run with zeros input", do_classify_zeros),
        MENU_ITEM('2', "Run with ring input", do_classify_ring),
        MENU_ITEM('3', "Run with slope input", do_classify_slope),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void magic_wand_menu() {
  magic_wand_init();
  menu_run(&MENU);
}
