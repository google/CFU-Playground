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
#include "metrics.h"
#include "models/magic_wand/model_magic_wand.h"
#include "tensorflow/lite/micro/examples/magic_wand/ring_micro_features_data.h"
#include "tensorflow/lite/micro/examples/magic_wand/slope_micro_features_data.h"
#include "tflite.h"

// The magic_wand model classifies based on the greatest of 4 scores.
typedef struct {
  uint32_t wing_score;  // Stored as uint32_t because we can't print floats.
  uint32_t ring_score;
  uint32_t slope_score;
  uint32_t negative_score;
} MagicWandResult;

// Initialize everything once
// deallocate tensors when done
static void magic_wand_init(void) {
  tflite_load_model(model_magic_wand, model_magic_wand_len);
}

// Run classification, after input has been loaded
MagicWandResult magic_wand_classify() {
  printf("Running magic_wand\n");
  DCACHE_SETUP_METRICS;
  tflite_classify();
  DCACHE_PRINT_METRICS;

  // Process the inference results.
  float* output = tflite_get_output_float();

  // Kindly ask for the raw bits of the floats.
  return (MagicWandResult){
      *(uint32_t*)&output[0],
      *(uint32_t*)&output[1],
      *(uint32_t*)&output[2],
      *(uint32_t*)&output[3],
  };
}

static int interpret_score(uint32_t& score) {
  return static_cast<int>(*reinterpret_cast<float*>(&score) * 1000000);
}

static void print_magic_wand_result(const char* prefix, MagicWandResult res) {
  printf("%s-- wing: 0x%lx, ring: 0x%lx, slope: 0x%lx, negative: 0x%lx\n",
         prefix, res.wing_score, res.ring_score, res.slope_score,
         res.negative_score);
  printf(
      "%s approx-- wing: 0.%06d ring: 0.%06d, slope: 0.%06d, negative: "
      "0.%06d\n",
      prefix, interpret_score(res.wing_score),
      interpret_score(res.ring_score),
      interpret_score(res.slope_score),
      interpret_score(res.negative_score));
}

static void do_classify_zeros() {
  puts("Classify all zeros input");
  tflite_set_input_zeros_float();
  print_magic_wand_result("  results", magic_wand_classify());
}

static void do_classify_ring() {
  puts("Classify ring");
  tflite_set_input_float(g_ring_micro_f9643d42_nohash_4_data);
  print_magic_wand_result("  results", magic_wand_classify());
}

static void do_classify_slope() {
  puts("Classify slope");
  tflite_set_input_float(g_slope_micro_f2e59fea_nohash_1_data);
  print_magic_wand_result("  results", magic_wand_classify());
}

#define NUM_GOLDEN 3

static void do_golden_tests() {
  // Dequantization leads to simpler floats.
  static MagicWandResult magic_wand_golden_results[NUM_GOLDEN] = {
      {0x3d200000, 0x3ee00000, 0x3db00000, 0x3ee00000},
      {0x0, 0x3f7f0000, 0x0, 0x0},
      {0x0, 0x0, 0x3f7f0000, 0x0},
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
    if (res.wing_score != exp.wing_score || res.ring_score != exp.ring_score ||
        res.slope_score != exp.slope_score ||
        res.negative_score != exp.negative_score) {
      failed = true;
      printf("*** Golden test %d failed: \n", i);
      print_magic_wand_result("actual", res);
      print_magic_wand_result("expected", exp);
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
