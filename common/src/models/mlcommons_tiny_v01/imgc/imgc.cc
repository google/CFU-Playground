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

#include "models/mlcommons_tiny_v01/imgc/imgc.h"

#include <stdio.h>

#include "menu.h"
#include "metrics.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_airplane.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_bird.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_car.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_cat.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_deer.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_dog.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_frog.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_horse.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_ship.h"
#include "models/mlcommons_tiny_v01/imgc/test_data/quant_truck.h"
#include "tflite.h"
#include "tiny/v0.1/training/image_classification/trained_models/pretrainedResnet_quant.h"

// The imgc model classifies images based on 10 categories
typedef struct {
  int8_t airplane_score;
  int8_t car_score;
  int8_t bird_score;
  int8_t cat_score;
  int8_t deer_score;
  int8_t dog_score;
  int8_t frog_score;
  int8_t horse_score;
  int8_t ship_score;
  int8_t truck_score;
} V01ImageClassificationResult;

#define NUM_GOLDEN 10

// Inputs and expected outputs for all test cases.
struct {
  const unsigned char* data;
  V01ImageClassificationResult actual;
} mlcommons_tiny_v01_ic_dataset[NUM_GOLDEN] = {
    {quant_airplane, {9, -128, -125, -128, -127, -116, -127, -31, -128, -124}},
    {quant_car, {-128, 127, -128, -128, -128, -128, -128, -128, -128, -128}},
    {quant_bird, {-128, -128, 127, -128, -128, -128, -128, -128, -128, -128}},
    {quant_cat, {-128, -128, -89, 54, -127, -101, -128, -121, -128, -128}},
    {quant_deer, {-128, -128, -128, -128, 109, -127, -110, -128, -128, -128}},
    {quant_dog, {-127, -128, -128, -121, -128, 120, -128, -128, -128, -128}},
    {quant_frog, {-128, -128, -128, -128, -128, -128, 127, -128, -128, -128}},
    {quant_horse, {-128, -128, -128, -128, -128, -128, -128, 127, -128, -128}},
    {quant_ship, {-128, -128, -128, -128, -128, -128, -128, -128, 127, -128}},
    {quant_truck, {-128, -128, -128, -128, -128, -128, -128, -128, -128, 127}},
};

static void imgc_init(void) {
  tflite_load_model(pretrainedResnet_quant, pretrainedResnet_quant_len);
}

V01ImageClassificationResult image_classify() {
  printf("Running imgc\n");
  DCACHE_SETUP_METRICS;
  tflite_classify();
  DCACHE_PRINT_METRICS;

  int8_t* output = tflite_get_output();
  return (V01ImageClassificationResult){
      output[0], output[1], output[2], output[3], output[4],
      output[5], output[6], output[7], output[8], output[9],
  };
}

static void print_imgc_result(const char* prefix,
                              V01ImageClassificationResult res) {
  printf(
      "%s-- airplane: %d, car: %d, bird: %d, cat: %d, deer: %d, dog: %d, "
      "frog: %d, horse: %d, ship: %d, truck: %d\n",
      prefix, res.airplane_score, res.car_score, res.bird_score, res.cat_score,
      res.deer_score, res.dog_score, res.frog_score, res.horse_score,
      res.ship_score, res.truck_score);
}

#define MLCOMMONS_TINY_V01_IMAGE_CLASSIFICATION_TEST(name, test_index) \
  static void name() {                                                 \
    puts(#name);                                                       \
    tflite_set_input(mlcommons_tiny_v01_ic_dataset[test_index].data);  \
    print_imgc_result("  result", image_classify());                   \
  }

// Smattering of tests for the menu, more can be easily added/removed.

MLCOMMONS_TINY_V01_IMAGE_CLASSIFICATION_TEST(do_classify_airplane, 0);
MLCOMMONS_TINY_V01_IMAGE_CLASSIFICATION_TEST(do_classify_car, 1);
MLCOMMONS_TINY_V01_IMAGE_CLASSIFICATION_TEST(do_classify_bird, 2);
MLCOMMONS_TINY_V01_IMAGE_CLASSIFICATION_TEST(do_classify_cat, 3);

#undef MLCOMMONS_TINY_V01_IMAGE_CLASSIFICATION_TEST

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; i < NUM_GOLDEN; i++) {
    tflite_set_input(mlcommons_tiny_v01_ic_dataset[i].data);
    V01ImageClassificationResult res = image_classify();
    V01ImageClassificationResult exp = mlcommons_tiny_v01_ic_dataset[i].actual;
    if (res.airplane_score != exp.airplane_score ||
        res.car_score != exp.car_score || res.bird_score != exp.bird_score ||
        res.cat_score != exp.cat_score || res.deer_score != exp.deer_score ||
        res.dog_score != exp.dog_score || res.frog_score != exp.frog_score ||
        res.horse_score != exp.horse_score ||
        res.ship_score != exp.ship_score ||
        res.truck_score != exp.truck_score) {
      failed = true;
      printf("*** Golden test %d failed: \n", i);
      print_imgc_result("actual", res);
      print_imgc_result("expected", exp);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

static struct Menu MENU = {
    "Tests for imgc model",
    "imgc",
    {
        MENU_ITEM('0', "Run with airplane input", do_classify_airplane),
        MENU_ITEM('1', "Run with car input", do_classify_car),
        MENU_ITEM('2', "Run with bird input", do_classify_bird),
        MENU_ITEM('3', "Run with cat input", do_classify_cat),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void mlcommons_tiny_v01_imgc_menu() {
  imgc_init();
  menu_run(&MENU);
}
