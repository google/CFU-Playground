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

#include "models/neural_net1/neural_net1.h"

#include <stdio.h>

#include "menu.h"
#include "models/neural_net1/model_neural_net1.h"
//#include "tensorflow/lite/micro/examples/magic_wand/ring_micro_features_data.h"
//#include "tensorflow/lite/micro/examples/magic_wand/slope_micro_features_data.h"
#include "tflite.h"

/*typedef struct {
  uint32_t wing_score;  // Stored as uint32_t because we can't print floats.
  uint32_t ring_score; 
  uint32_t slope_score;
  uint32_t negative_score;
} MagicWandResult;
*/

// Initialize everything once
// deallocate tensors when done
static void neural_net1_init(void) {
  tflite_load_model(model_neural_net1_tflite, model_neural_net1_tflite_len);
}

// Run classification, after input has been loaded
/*MagicWandResult magic_wand_classify() {
  printf("Running magic_wand\n");
  tflite_classify();

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

*/
#define NUM_GOLDEN 3

/*static void do_golden_tests() {
  
}
*/
static void test() {
printf("hi");

}
static struct Menu MENU = {
    "Tests for MNIST neural_net1 model",
    "neural_net1",
    {
        MENU_ITEM('1', "Test- say hi", test),
        MENU_END,
    },
};

// For integration into menu system
void neural_net1_menu() {
  neural_net1_init();
  menu_run(&MENU);
}
