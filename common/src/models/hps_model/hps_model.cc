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
#include "models/hps_model/hps_0.h"
#include "models/hps_model/hps_1.h"
#include "models/hps_model/hps_2.h"
#include "models/hps_model/hps_model_2021_09_20_tiled.h"
#include "models/hps_model/hps_model_2022_01_05_74ops.h"
#include "models/hps_model/hps_model_2022_01_05_89ops.h"
#include "models/hps_model/presence_0_320_240_1_20220117_140437_201k_26k_96ops.h"
#include "models/hps_model/presence_0_320_240_1_20220415_172145_201k_26k_96ops.h"
#include "models/hps_model/second_0_320_240_1_20220117_135512_201k_26k_96ops.h"
#include "models/hps_model/second_0_320_240_1_20220416_163802_201k_26k_96ops.h"
#include "models/hps_model/shared_20220623_1032_tiled.h"
#include "tflite.h"
namespace {

int loaded_model = 0;
int num_outputs = 1;

struct ModelResult {
  int8_t score1;
  int8_t score2;  // not produced by all models
};

void print_result(const ModelResult& result) {
  switch (num_outputs) {
    case 2:
      printf("Result is (%d, %d)\n", result.score1, result.score2);
      break;
    case 1:
    default:
      printf("Result is (%d)\n", result.score1);
      break;
  }
}

// Initialize model
void do_init_09_20(void) {
  puts("Loading HPS 09_20 model");
  tflite_load_model(hps_model_2021_09_20_tiled, hps_model_2021_09_20_tiled_len);
  loaded_model = 0;
  num_outputs = 1;
}

// Initialize model
void do_init_01_05_74ops(void) {
  puts("Loading HPS 01_05_74ops model");
  tflite_load_model(hps_model_2022_01_05_74ops, hps_model_2022_01_05_74ops_len);
  loaded_model = 1;
  num_outputs = 1;
}

// Initialize model
void do_init_01_05_89ops(void) {
  puts("Loading HPS 01_05_89ops model");
  tflite_load_model(hps_model_2022_01_05_89ops, hps_model_2022_01_05_89ops_len);
  loaded_model = 2;
  num_outputs = 1;
}

// Initialize model
void do_init_presence_2022017_96ops(void) {
  puts("Loading Presence 20220117 96ops model");
  tflite_load_model(presence_0_320_240_1_20220117_140437_201k_26k_96ops,
                    presence_0_320_240_1_20220117_140437_201k_26k_96ops_len);
  loaded_model = 3;
  num_outputs = 1;
}

// Initialize model
void do_init_second_2022017_96ops(void) {
  puts("Loading Second 20220117 96ops model");
  tflite_load_model(second_0_320_240_1_20220117_135512_201k_26k_96ops,
                    second_0_320_240_1_20220117_135512_201k_26k_96ops_len);
  loaded_model = 4;
  num_outputs = 1;
}

// Initialize model
void do_init_presence_20220415_96ops(void) {
  puts("Loading Presence 20220415 96ops model");
  tflite_load_model(presence_0_320_240_1_20220415_172145_201k_26k_96ops,
                    presence_0_320_240_1_20220415_172145_201k_26k_96ops_len);
  loaded_model = 5;
  num_outputs = 1;
}

// Initialize model
void do_init_second_20220416_96ops(void) {
  puts("Loading Second 20220416 96ops model");
  tflite_load_model(second_0_320_240_1_20220416_163802_201k_26k_96ops,
                    second_0_320_240_1_20220416_163802_201k_26k_96ops_len);
  loaded_model = 6;
  num_outputs = 1;
}

// Initialize model
void do_init_shared_20220623_1032_tiled(void) {
  puts("Loading shared 20220623 model");
  tflite_load_model(shared_20220623_1032_tiled, shared_20220623_1032_tiled_len);
  loaded_model = 7;
  num_outputs = 2;
}

// Run classification and interpret results
ModelResult classify() {
  tflite_classify();
  int8_t* output = tflite_get_output();
  switch (num_outputs) {
    case 2:
      return ModelResult{output[0], output[1]};
    case 1:
    default:
      return ModelResult{output[0], 0};
  }
}

// Classify with random data
ModelResult classify_cat() {
  tflite_set_input_unsigned(cat_picture);
  return classify();
}

void do_classify_cat() { print_result(classify_cat()); }

// Classify with a grid pattern
ModelResult classify_diagram() {
  tflite_set_input_unsigned(diagram);
  return classify();
}

void do_classify_diagram() { print_result(classify_diagram()); }

// Set input to zero and run classification
ModelResult classify_zeros() {
  tflite_set_input_zeros();
  return classify();
}

void do_classify_zeros() { print_result(classify_zeros()); }

// Classify hps_* inputs

ModelResult classify_hps_0() {
  tflite_set_input_unsigned(hps_0);
  return classify();
}

void do_classify_hps_0() { print_result(classify_hps_0()); }

ModelResult classify_hps_1() {
  tflite_set_input_unsigned(hps_1);
  return classify();
}

void do_classify_hps_1() { print_result(classify_hps_1()); }

ModelResult classify_hps_2() {
  tflite_set_input_unsigned(hps_2);
  return classify();
}

void do_classify_hps_2() { print_result(classify_hps_2()); }

// Golden tests: expected results
struct GoldenTest {
  ModelResult (*fn)();
  const char* name;
  ModelResult expected[8];
};

GoldenTest golden_tests[] = {
    {classify_cat,
     "cat",
     {{-77, 0},
      {-47, 0},
      {-47, 0},
      {-101, 0},
      {-117, 0},
      {-100, 0},
      {-108, 0},
      {-112, -125}}},
    {classify_diagram,
     "diagram",
     {{-124, 0},
      {-123, 0},
      {-123, 0},
      {-124, 0},
      {-127, 0},
      {-117, 0},
      {-127, 0},
      {-128, -128}}},
    {classify_zeros,
     "zeroes",
     {{-126, 0},
      {-128, 0},
      {-128, 0},
      {-128, 0},
      {-128, 0},
      {-109, 0},
      {-126, 0},
      {-119, -124}}},
    {classify_hps_0,
     "hps_0",
     {{-119, 0},
      {-75, 0},
      {-75, 0},
      {-73, 0},
      {-125, 0},
      {-115, 0},
      {-128, 0},
      {-91, -128}}},
    {classify_hps_1,
     "hps_1",
     {{124, 0},
      {127, 0},
      {127, 0},
      {121, 0},
      {-119, 0},
      {127, 0},
      {-128, 0},
      {127, -128}}},
    {classify_hps_2,
     "hps_2",
     {{126, 0},
      {127, 0},
      {127, 0},
      {125, 0},
      {127, 0},
      {127, 0},
      {127, 0},
      {127, 127}}},
    {nullptr, "", 0},
};

static void do_golden_tests() {
  bool failed = false;
  for (size_t i = 0; golden_tests[i].fn; i++) {
    const GoldenTest& test = golden_tests[i];
    printf("Testing input %s: ", test.name);
    ModelResult actual = test.fn();
    ModelResult expected = test.expected[loaded_model];
    if (actual.score1 != expected.score1) {
      failed = true;
      printf("FAIL score1 %d (actual) != %d (expected) ***\n", actual.score1,
             expected.score1);
    } else if (actual.score2 != expected.score2) {
      failed = true;
      printf("FAIL score2 %d (actual) != %d (expected) ***\n", actual.score2,
             expected.score2);
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
        MENU_ITEM('a', "Cat picture input", do_classify_cat),
        MENU_ITEM('b', "Diagram input", do_classify_diagram),
        MENU_ITEM('c', "Zeros input", do_classify_zeros),
        MENU_ITEM('d', "hps_0", do_classify_hps_0),
        MENU_ITEM('e', "hps_1", do_classify_hps_1),
        MENU_ITEM('f', "hps_2", do_classify_hps_2),
        MENU_ITEM('g', "Golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_ITEM('0', "Reinitialize with 09_20 model", do_init_09_20),
        MENU_ITEM('1', "Reinitialize with 01_05_74ops model",
                  do_init_01_05_74ops),
        MENU_ITEM('2', "Reinitialize with 01_05_89ops model",
                  do_init_01_05_89ops),
        MENU_ITEM('3', "Reinitialize with presence_2022017_96ops model",
                  do_init_presence_2022017_96ops),
        MENU_ITEM('4', "Reinitialize with second_2022017_96ops model",
                  do_init_second_2022017_96ops),
        MENU_ITEM('5', "Reinitialize with presence_20220415_96ops model",
                  do_init_presence_20220415_96ops),
        MENU_ITEM('6', "Reinitialize with second_20220416_96ops model",
                  do_init_second_20220416_96ops),
        MENU_ITEM('7', "Reinitialize with shared_20220623_1032_tiled model",
                  do_init_shared_20220623_1032_tiled),
        MENU_END,
    },
};

}  // anonymous namespace

// For integration into menu system
extern "C" void hps_model_menu() {
  do_init_shared_20220623_1032_tiled();
  menu_run(&MENU);
}
