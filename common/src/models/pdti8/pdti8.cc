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

#include "models/pdti8/pdti8.h"

#include <stdio.h>

#include "menu.h"
#include "models/pdti8/model_pdti8.h"
#include "tensorflow/lite/micro/examples/person_detection/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection/person_image_data.h"
#include "tflite.h"

extern "C" {
#include "fb_util.h"
};

// Initialize everything once
// deallocate tensors when done
static void pdti8_init(void) {
  tflite_load_model(model_pdti8, model_pdti8_len);
}

// Run classification, after input has been loaded
static int32_t pdti8_classify() {
  printf("Running pdti8\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = tflite_get_output();
  printf("OUT: %d\n",output[0]);
  return output[1] - output[0];
  
}

static void do_classify_zeros() {
  tflite_set_input_zeros();
  int32_t result = pdti8_classify();
  printf("  result is %ld\n", result);
}

static void do_classify_no_person() {
  puts("Classify Not Person");
  tflite_set_input(g_no_person_data);
  int32_t result = pdti8_classify();
  printf("  result is %ld\n", result);
  
#ifdef CSR_VIDEO_FRAMEBUFFER_BASE
  char msg_buff[256] = { 0 };

  snprintf(msg_buff, sizeof(msg_buff), "Result is %ld", result);
  fb_clear();
  fb_draw_string(0,  10, 0x007FFF00, "Classify Not Person");
  fb_draw_buffer(0,  50, 96, 96, (const uint8_t *)g_no_person_data, 1);
  fb_draw_string(0, 220, 0x007FFF00, (const char *)msg_buff);
  flush_cpu_dcache();
  flush_l2_cache();
#endif  
}

static void do_classify_person() {
  puts("Classify Person");
  tflite_set_input(g_person_data);
  int32_t result = pdti8_classify();
  printf("  result is %ld\n", result);

#ifdef CSR_VIDEO_FRAMEBUFFER_BASE
  char msg_buff[256] = { 0 };

  snprintf(msg_buff, sizeof(msg_buff), "Result is %ld", result);
  fb_clear();
  fb_draw_string(0,  10, 0x007FFF00, "Classify Person");
  fb_draw_buffer(0,  50, 96, 96, (const uint8_t *)g_person_data, 1);
  fb_draw_string(0, 220, 0x007FFF00, (const char *)msg_buff);
  flush_cpu_dcache();
  flush_l2_cache();
#endif  
}

#define NUM_GOLDEN 3
static int32_t golden_results[NUM_GOLDEN] = {-144, 50, 226};

static void do_golden_tests() {
  int32_t actual[NUM_GOLDEN];

  tflite_set_input_zeros();
  actual[0] = pdti8_classify();

  tflite_set_input(g_no_person_data);
  actual[1] = pdti8_classify();

#ifdef CSR_VIDEO_FRAMEBUFFER_BASE
  char msg_buff[256] = { 0 };

  fb_clear();
  fb_draw_string(0,  10, 0x007FFF00, "Classify Not Person");
  fb_draw_buffer(0,  50, 96, 96, (const uint8_t *)g_no_person_data, 1);
  memset(msg_buff, 0x00, sizeof(msg_buff));
  snprintf(msg_buff, sizeof(msg_buff), "Result is %ld, Expected is %ld", actual[1], golden_results[1]);
  fb_draw_string(0, 220, 0x007FFF00, (const char *)msg_buff);
  flush_cpu_dcache();
  flush_l2_cache();
#endif 
  
  tflite_set_input(g_person_data);
  actual[2] = pdti8_classify();

#ifdef CSR_VIDEO_FRAMEBUFFER_BASE
  fb_clear();
  fb_draw_string(0,  10, 0x007FFF00, "Classify Person");
  fb_draw_buffer(0,  50, 96, 96, (const uint8_t *)g_person_data, 1);
  memset(msg_buff, 0x00, sizeof(msg_buff));
  snprintf(msg_buff, sizeof(msg_buff), "Result is %ld, Expected is %ld", actual[2], golden_results[2]);
  fb_draw_string(0, 220, 0x007FFF00, (const char *)msg_buff);
  flush_cpu_dcache();
  flush_l2_cache();
#endif 

  bool failed = false;
  for (size_t i = 0; i < NUM_GOLDEN; i++) {
    if (actual[i] != golden_results[i]) {
      failed = true;
      printf("*** Golden test %d failed: %ld (actual) != %ld (expected))\n", i,
             actual[i], golden_results[i]);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

static struct Menu MENU = {
    "Tests for pdti8 model",
    "pdti8",
    {
        MENU_ITEM('1', "Run with zeros input", do_classify_zeros),
        MENU_ITEM('2', "Run with no-person input", do_classify_no_person),
        MENU_ITEM('3', "Run with person input", do_classify_person),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void pdti8_menu() {
  pdti8_init();

#ifdef CSR_VIDEO_FRAMEBUFFER_BASE
  fb_init();
  flush_cpu_dcache();
  flush_l2_cache();
#endif
  
  menu_run(&MENU);
}
