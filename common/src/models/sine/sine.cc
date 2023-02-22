#include "models/sine/sine.h"

#include <math.h>
#include <stdio.h>

#include "menu.h"
#include "models/sine/model_sine.h"
#include "tensorflow/lite/micro/examples/person_detection/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection/person_image_data.h"
#include "playground_util/models_utils.h"
#include "tflite.h"

extern "C" {
#include "fb_util.h"
};

// Initialize everything once
// deallocate tensors when done

// static void

#define SINE_MAX(x, y) (((x) >= (y)) ? (x) : (y))
#define SINE_MIN(x, y) (((x) <= (y)) ? (x) : (y))

static void sine_init(void) { tflite_load_model(sine_model, sine_model_len); }

// static int8_t quantize(float x) {
//   int8_t x_quantized = x / tflite_input_scale() + tflite_input_zero_point();
//   return x_quantized;
// }

// static float dequantize(int8_t y_pred_quantized) {
//   float y_pred = (y_pred_quantized - tflite_output_zero_point()) * tflite_output_scale();
//   return y_pred;
// }

// Run classification, after input has been loaded
static float sine_classify() {
  printf("Running sine model\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = tflite_get_output();

  int8_t y_pred_quantized = output[0];
  float y_pred = dequantize(y_pred_quantized);
  return y_pred;
}

#define NUM_TEST 4
static float sine_x[NUM_TEST] = {0.0f, 1.f, 3.f, 5.f};

static void do_tests() {
  float epsilon = 0.05f;
  bool failed = false;

  for (size_t i = 0; i < NUM_TEST; ++i) {
    float x = sine_x[i];
    int8_t input_data[1];

    // Set input
    int8_t x_quantized = quantize(x);
    input_data[0] = x_quantized;
    tflite_set_input(input_data);
    // interpreter->input(0)->data.int8[0] = x_quantized;

    // Get output
    float y_pred = sine_classify();
    float y_true = sin(x);

    int32_t* x_casted_ptr = (int32_t*) &x;
    int32_t* y_pred_casted_ptr = (int32_t*) &y_pred;
    int32_t* y_true_casted_ptr = (int32_t*) &y_true;

    // printf("sine_mode(%.6f) = %.6f\n", (double) x, (double) y_pred);
    // printf("sin(%.6f) = %.6f\n", (double) x, (double) y_true);
    printf("sine_mode(%ld) = %ld\n", *x_casted_ptr, *y_pred_casted_ptr);
    printf("sin(%ld) = %ld\n", *x_casted_ptr, *y_true_casted_ptr);

    float delta = SINE_MAX(y_true, y_pred) - SINE_MIN(y_true, y_pred);
    if (delta > epsilon) {
      failed = true;
      printf("*** Sine test %d failed: %.6f (actual) != %.6f (expected))\n", i,
             (double) y_pred, (double) y_true);
    }
  }

  if (failed) {
    printf("FAIL Sine tests failed\n");
  } else {
    printf("OK   Sine tests passed\n");
  }
}

static struct Menu MENU = {
    "Tests for sine model",
    "sine",
    {
        MENU_ITEM('g', "Run sine tests (check for expected outputs)", do_tests),
        MENU_END,
    },
};

// For integration into menu system
void sine_menu() {
  sine_init();
  menu_run(&MENU);
}
