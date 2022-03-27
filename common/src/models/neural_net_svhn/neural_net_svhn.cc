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

#include "models/neural_net_svhn/neural_net_svhn.h"

#include <stdio.h>

#include "menu.h"
#include "models/neural_net_svhn/model_neural_net_svhn.h"
#include "/home/shivaubuntu/Tensorflow/neural_net_svhn/svhn_img_data.cc"
#include "tflite.h"


extern "C" {
#include "fb_util.h"
};


// Initialize everything once
// deallocate tensors when done
static void neural_net_svhn_init(void) {
  tflite_load_model(model_neural_net_svhn_tflite, model_neural_net_svhn_tflite_len);
}

// Run classification, after input has been loaded
static int32_t neural_net_svhn_classify() {
  printf("Running neural_net_svhn\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = tflite_get_output();
  int8_t max_conf=0;
  int i_conf;
  int i=0;
  for(;i<10;i++)
  {
    printf("conf lvl for %d  : %d\n",i,output[i]);
    if(output[i]>max_conf)
      {max_conf=output[i];
      i_conf = i;
      }
  }  
  return i_conf;
  
}


#define NUM_GOLDEN 2
static int32_t golden_results[NUM_GOLDEN] = {0, 5};

static void do_golden_tests() {
  int32_t actual[NUM_GOLDEN];


  tflite_set_input_zeros();
  actual[0] = neural_net_svhn_classify();
  printf("output @ all 0s inp: %ld", actual[0]);
  tflite_set_input(g_svhn_img_data);
  actual[1] = neural_net_svhn_classify();
  
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
    "Tests for SVHN neural_net_svhn model",
    "neural_net_svhn",
    {
        MENU_ITEM('1', "Test- say hi", test),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void neural_net_svhn_menu() {
  neural_net_svhn_init();
  
  #ifdef CSR_VIDEO_FRAMEBUFFER_BASE
  fb_init();
  flush_cpu_dcache();
  flush_l2_cache();
#endif

  menu_run(&MENU);
}
