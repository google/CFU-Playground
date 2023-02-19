#include "models/signal_modulation_2/signal_modulation_2.h"

#include <math.h>
#include <stdio.h>

#include "menu.h"
#include "models/signal_modulation_2/model_signal_modulation_2.h"
#include "models/signal_modulation_2/test_data.h"
#include "tensorflow/lite/micro/examples/person_detection/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection/person_image_data.h"
#include "tflite.h"

extern "C" {
#include "fb_util.h"
};

// Initialize everything once
// deallocate tensors when done

// static void

#define SM1_MAX(x, y) (((x) >= (y)) ? (x) : (y))
#define SM1_MIN(x, y) (((x) <= (y)) ? (x) : (y))
// typedef size_t uint32_t;

static void signal_modulation_2_init(void) {
  tflite_load_model(signal_modulation_2_model, signal_modulation_2_model_len);
}

// Run classification, after input has been loaded
static float* signal_modulation_2_classify() {
  printf("Running signal_modulation_2 model\n");
  tflite_classify();

  // Process the inference results.
  float* output = (float*)tflite_get_output();
  return output;
}

#define NUM_CLASSES 11

/* Returns true if failed */
static bool perform_one_test(float* input, float* expected_output,
                             float epsilon) {
  bool failed = false;
  tflite_set_input(input);
  float* output = signal_modulation_2_classify();
  for (size_t i = 0; i < NUM_CLASSES; ++i) {
    float y_true = expected_output[i];
    float y_pred = output[i];
    float delta = SM1_MAX(y_true, y_pred) - SM1_MIN(y_true, y_pred);

    int* y_true_u32 = (int*)(&y_true);
    int* y_pred_u32 = (int*)(&y_pred);
    if (delta > epsilon) {
      printf(
          "*** Signal modulation 1 test failed %d (actual) != %d (pred). "
          "Class=%u\n",
          *y_true_u32, *y_pred_u32, i);
      failed = true;
    } else {
      printf(
          "+++ Signal modulation 1 test success %d (actual) != %d (pred). "
          "Class=%u\n",
          *y_true_u32, *y_pred_u32, i);
    }
  }
  return failed;
}

static void do_tests() {
  float epsilon = 0.00005f;
  bool failed = false;

  failed =
      failed || perform_one_test(test_data_16QAM_7_signal_modulation_2,
                                 pred_16QAM_7_signal_modulation_2, epsilon);

  if (failed) {
    printf("FAIL Signal modulation 1 tests failed\n");
  } else {
    printf("OK   Signal modulation 1 tests passed\n");
  }
}

static struct Menu MENU = {
    "Tests for Signal modulation 2 model",
    "signal_modulation_2",
    {
        MENU_ITEM('g',
                  "Run Signal modulation 2 tests (check for expected outputs)",
                  do_tests),
        MENU_END,
    },
};

// For integration into menu system
void signal_modulation_2_menu() {
  signal_modulation_2_init();
  menu_run(&MENU);
}
