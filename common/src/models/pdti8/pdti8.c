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
#include "tensorflow/lite/micro/examples/person_detection_experimental/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection_experimental/person_image_data.h"
#include "tflite.h"

const char shades[16] = {' ', '.', ',', '-', '+', '/', 'x', 'L',
                         'r', 'n', 'm', '0', 'O', 'M', '#', '@'};

// Initialize everything once
// deallocate tensors when done
static void pdti8_init(void) { tflite_load_model(model_pdti8); }

// Get pixel of input image
int8_t get_pixel(size_t x, size_t y)
{
    int8_t *inbuf = tflite_get_input();
    return inbuf[y*96+x];
}


// Load image from frame buffer and show
void show_hires() {
  printf("start\n");
  int min=0;
  int max=0;
  for (size_t in_y = 0; in_y < 96; in_y+=2) {
    for (size_t in_x = 0; in_x < 96; in_x++) {
      int val = get_pixel(in_x, in_y);
      if (val<min) min = val;
      if (val>max) max = val;
    }
  }
  int stepsize = (max-min) / 16;

  for (size_t in_y = 0; in_y < 96; in_y+=2) {
    char line[100];
    line[96] = 0;
    for (size_t in_x = 0; in_x < 96; in_x++) {
      int val = get_pixel(in_x, in_y);
      int s = ((val - min) / stepsize);
      if (s<0) s=0;
      if (s>15) s=15;
      line[in_x] = shades[s];
    }
    puts(line);
  }
  printf("end\n");
}


// Run classification, after input has been loaded
static int32_t pdti8_classify() {
  printf("Running pdti8\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = tflite_get_output();
  return output[1] - output[0];
}

// use uploaded images
static void do_classify_uploaded(uint8_t *data) {
  tflite_set_input_unsigned(data);
  show_hires();
  int32_t result = pdti8_classify();
  printf("  result is %ld\n", result);
}

static void do_classify_uploaded_0() {
  uint8_t *data = (uint8_t *)(0x41000000);
  do_classify_uploaded(data);
}

static void do_classify_uploaded_1() {
  uint8_t *data = (uint8_t *)(0x41100000);
  do_classify_uploaded(data);
}

static void do_classify_uploaded_2() {
  uint8_t *data = (uint8_t *)(0x41200000);
  do_classify_uploaded(data);
}

// ZEROS
static void do_classify_zeros() {
  tflite_set_input_zeros();
  int32_t result = pdti8_classify();
  printf("  result is %ld\n", result);
}

// NO PERSON
static void do_classify_no_person() {
  puts("Classify Not Person");
  tflite_set_input(g_no_person_data);
  show_hires();
  int32_t result = pdti8_classify();
  printf("  result is %ld\n", result);
}

// PERSON
static void do_classify_person() {
  puts("Classify Person");
  tflite_set_input(g_person_data);
  show_hires();
  int32_t result = pdti8_classify();
  printf("  result is %ld\n", result);
}

#define NUM_GOLDEN 3
static int32_t golden_results[NUM_GOLDEN] = {-144, 50, 226};

static void do_golden_tests() {
  int32_t actual[NUM_GOLDEN];
  tflite_set_input_zeros();
  actual[0] = pdti8_classify();
  tflite_set_input(g_no_person_data);
  actual[1] = pdti8_classify();
  tflite_set_input(g_person_data);
  actual[2] = pdti8_classify();

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
        MENU_ITEM('a', "Run with uploaded image 0", do_classify_uploaded_0),
        MENU_ITEM('b', "Run with uploaded image 1", do_classify_uploaded_1),
        MENU_ITEM('c', "Run with uploaded image 2", do_classify_uploaded_2),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void pdti8_menu() {
  pdti8_init();
  menu_run(&MENU);
}
