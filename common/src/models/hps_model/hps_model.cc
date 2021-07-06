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
int32_t classify() {
  printf("Running an hps model\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = tflite_get_output();
  return (int32_t)output[1] - (int32_t)output[0];
}

// Set input to zero and run classification
void do_classify_zeros() {
  tflite_set_input_zeros();
  int32_t result = classify();
  printf("Result is %ld\n", result);
}

struct Menu MENU = {
    "Tests for HPS model model",
    "hps",
    {
        MENU_ITEM('z', "Run with zeros input", do_classify_zeros),
        MENU_END,
    },
};

}  // anonymous namespace

// For integration into menu system
extern "C" void hps_model_menu() {
  init();
  menu_run(&MENU);
}
