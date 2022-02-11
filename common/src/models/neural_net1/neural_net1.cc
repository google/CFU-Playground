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
#include "/home/shivaubuntu/CFU-Playground/CFU-Playground/Custom_Tensorflow/mnist_test_data/mnist_img_data.cc"
#include "tflite.h"


extern "C" {
#include "fb_util.h"
};


// Initialize everything once
// deallocate tensors when done
static void neural_net1_init(void) {
  tflite_load_model(model_neural_net1_tflite, model_neural_net1_tflite_len);
}

// Run classification, after input has been loaded
static int32_t neural_net1_classify() {
  printf("Running neural_net1\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = tflite_get_output();
  int8_t max_conf=0;
  for(int i=0;i<10;i++)
  {
    if(output[i]>=output[max_conf])
      max_conf = i;
    printf("conf lvl for %d : %d\n",i,output[i]);
  }
  printf("OUT: %d\n",max_conf);
  return max_conf;
  
}


#define NUM_GOLDEN 2
static int32_t golden_results[NUM_GOLDEN] = {0, 2};

static void do_golden_tests() {
  int32_t actual[NUM_GOLDEN];


  tflite_set_input_zeros();
  actual[0] = neural_net1_classify();
  printf("output @ all 0s inp: %ld", actual[0]);
  tflite_set_input(g_mnist_img_data);
  actual[1] = neural_net1_classify();
  
  #ifdef CSR_VIDEO_FRAMEBUFFER_BASE
  char msg_buff[256] = { 0 };
  fb_clear();
  memset(msg_buff, 0x00, sizeof(msg_buff));
  snprintf(msg_buff, sizeof(msg_buff), "Result is %ld, Expected is %ld", actual[1],  golden_results[1]);
  flush_cpu_dcache();
  flush_l2_cache();
#endif 

  if(actual[1]!= golden_results[1])
    printf("Failed golden test..check again");


  
}


static void test() {
printf("hi");

}
static struct Menu MENU = {
    "Tests for MNIST neural_net1 model",
    "neural_net1",
    {
        MENU_ITEM('1', "Test- say hi", test),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void neural_net1_menu() {
  neural_net1_init();
  
  #ifdef CSR_VIDEO_FRAMEBUFFER_BASE
  fb_init();
  flush_cpu_dcache();
  flush_l2_cache();
#endif

  menu_run(&MENU);
}
