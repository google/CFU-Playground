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

#include "models/micro_speech/micro_speech.h"

#include <stdio.h>

#include "menu.h"
#include "metrics.h"
#include "models/micro_speech/model_micro_speech.h"
#include "tensorflow/lite/micro/examples/micro_speech/micro_features/no_micro_features_data.h"
#include "tensorflow/lite/micro/examples/micro_speech/micro_features/yes_micro_features_data.h"
#include "tflite.h"

// The micro_speech model classifies speech based on the greatest of 4 scores.
typedef struct {
  uint8_t silence_score;
  uint8_t unknown_score;
  uint8_t yes_score;
  uint8_t no_score;
} MicroSpeechResult;

// Initialize everything once
// deallocate tensors when done
static void micro_speech_init(void) {
  tflite_load_model(model_micro_speech, model_micro_speech_len);
}

// Run classification, after input has been loaded
MicroSpeechResult micro_speech_classify() {
  printf("Running micro_speech\n");
  PERF_SETUP_METRICS;
  tflite_classify();
  PERF_PRINT_METRICS;

  // Process the inference results.
  int8_t* output = tflite_get_output();
  return (MicroSpeechResult){
      static_cast<uint8_t>(output[0] + 128),
      static_cast<uint8_t>(output[1] + 128),
      static_cast<uint8_t>(output[2] + 128),
      static_cast<uint8_t>(output[3] + 128),
  };
}

static void do_classify_zeros() {
  tflite_set_input_zeros();
  MicroSpeechResult res = micro_speech_classify();
  printf("  results-- silence: %d, unkown: %d, yes: %d, no: %d\n",
         res.silence_score, res.unknown_score, res.yes_score, res.no_score);
}

static void do_classify_no() {
  puts("Classify \"no\"");
  tflite_set_input(g_no_micro_f9643d42_nohash_4_data);
  MicroSpeechResult res = micro_speech_classify();
  printf("  results-- silence: %d, unkown: %d, yes: %d, no: %d\n",
         res.silence_score, res.unknown_score, res.yes_score, res.no_score);
}

static void do_classify_yes() {
  puts("Classify \"yes\"");
  tflite_set_input(g_yes_micro_f2e59fea_nohash_1_data);
  MicroSpeechResult res = micro_speech_classify();
  printf("  results-- silence: %d, unkown: %d, yes: %d, no: %d\n",
         res.silence_score, res.unknown_score, res.yes_score, res.no_score);
}

#define NUM_GOLDEN 3

static void do_golden_tests() {
  static MicroSpeechResult micro_speech_golden_results[NUM_GOLDEN] = {
      {0, 7, 8, 241},
      {0, 14, 0, 242},
      {0, 0, 255, 0},
  };

  MicroSpeechResult actual[NUM_GOLDEN];
  tflite_set_input_zeros();
  actual[0] = micro_speech_classify();
  tflite_set_input(g_no_micro_f9643d42_nohash_4_data);
  actual[1] = micro_speech_classify();
  tflite_set_input(g_yes_micro_f2e59fea_nohash_1_data);
  actual[2] = micro_speech_classify();

  bool failed = false;
  for (size_t i = 0; i < NUM_GOLDEN; i++) {
    MicroSpeechResult res = actual[i];
    MicroSpeechResult exp = micro_speech_golden_results[i];
    if (res.silence_score != exp.silence_score ||
        res.unknown_score != exp.unknown_score ||
        res.yes_score != exp.yes_score || res.no_score != exp.no_score) {
      failed = true;
      printf("*** Golden test %d failed: \n", i);
      printf("actual-- silence: %d, unkown: %d, yes: %d, no: %d\n",
             res.silence_score, res.unknown_score, res.yes_score, res.no_score);
      printf("expected-- silence: %d, unkown: %d, yes: %d, no: %d\n",
             exp.silence_score, exp.unknown_score, exp.yes_score, exp.no_score);
    }
  }

  if (failed) {
    puts("FAIL Golden tests failed");
  } else {
    puts("OK   Golden tests passed");
  }
}

static struct Menu MENU = {
    "Tests for micro_speech model",
    "micro_speech",
    {
        MENU_ITEM('1', "Run with zeros input", do_classify_zeros),
        MENU_ITEM('2', "Run with \"no\" input", do_classify_no),
        MENU_ITEM('3', "Run with \"yes\" input", do_classify_yes),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)",
                  do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void micro_speech_menu() {
  micro_speech_init();
  menu_run(&MENU);
}
