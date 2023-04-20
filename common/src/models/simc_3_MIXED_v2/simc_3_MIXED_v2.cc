#include "models/simc_3_MIXED_v2/simc_3_MIXED_v2.h"

#include <math.h>
#include <stdio.h>

#include "menu.h"
#include "models/simc_3_MIXED_v2/simc_3_MIXED_v2_model.h"
#include "models/simc_3_MIXED_v2/simc_3_MIXED_v2_test_data.h"
#include "playground_util/models_utils.h"
#include "tensorflow/lite/micro/examples/person_detection/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection/person_image_data.h"
//
// #include "playground_util/models_utils.h"
//

#include "cfu.h"
#include "perf.h"
#include "tflite.h"

extern "C" {
#include "fb_util.h"
};

#ifndef CFU_MAX
#define CFU_MAX(x, y) (((x) >= (y)) ? (x) : (y))
#endif  // CFU_MAX

#ifndef CFU_MIN
#define CFU_MIN(x, y) (((x) <= (y)) ? (x) : (y))
#endif  // CFU_MIN

// This method creates interpreter, arena, loads model to memory
static void simc_3_MIXED_v2_init(void) {
  tflite_load_model(simc_3_MIXED_v2_model, simc_3_MIXED_v2_model_len);
}

// float dequantized_output[11];

// Run classification, after input has been loaded
static int8_t* simc_3_MIXED_v2_classify() {
  printf("Running simc_3_MIXED_v2 model classification\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = (int8_t*)tflite_get_output();
  return output;
}

#define NUM_CLASSES 11

/* Returns true if failed */
[[maybe_unused]] static bool perform_one_test(int8_t* input,
                                              int8_t* expected_output,
                                              int8_t epsilon) {
  bool failed = false;
  tflite_set_input(input);
  int8_t* output = simc_3_MIXED_v2_classify();
  for (size_t i = 0; i < NUM_CLASSES; ++i) {
    int8_t y_true = expected_output[i];
    int8_t y_pred = output[i];
    // printf("expected[%d] = %d, actual[%d] = %d\n", i, y_true, i, y_pred);

    int32_t delta = CFU_MAX(y_true, y_pred) - CFU_MIN(y_true, y_pred);
    // printf("epsilon = %d, delta = %ld, max=%d, min=%d\n", epsilon, delta,
    //   CFU_MAX(y_true, y_pred), CFU_MIN(y_true, y_pred));
    if (delta > epsilon) {
      printf(
          "*** simc_3_MIXED_v2 test failed %d (actual) != %d (pred). "
          "Class=%u\n",
          y_true, y_pred, i);

      failed = true;
    } else {
    }
  }
  return failed;
}

#ifndef CFU_CONV1d_V8_PARAMS
#define CFU_CONV1d_V8_PARAMS

#define CFU_INITIALIZE 0
#define CFU_WRITE_INPUT_BUFFER 1
#define CFU_WRITE_FILTER_BUFFER 2
#define CFU_WRITE_INPUT_OFFSET 3
#define CFU_WRITE_INPUT_OUTPUT_WIDTH 4
#define CFU_WRITE_INPUT_DEPTH 5
#define CFU_START_COMPUTATION 6
#define CFU_READ_ACCUMULATOR 7
#define CFU_WRITE_START_FILTER_X 8
#define CFU_FINISHED 9

// Temporaty
#define CFU_READ_INPUT_BUFFER 10
#define CFU_READ_FILTER_BUFFER 11

#endif  // CFU_CONV1d_V8_PARAMS

void printBits(size_t const size, void const* const ptr) {
  unsigned char* b = (unsigned char*)ptr;
  unsigned char byte;
  int i, j;

  for (i = size - 1; i >= 0; i--) {
    for (j = 7; j >= 0; j--) {
      byte = (b[i] >> j) & 1;
      printf("%u", byte);
    }
  }
  puts("");
}

[[maybe_unused]] static void test_assert_equal(int8_t v1, int8_t v2, const char* msg = "") {
  if (v1 == v2)
    return;
  printf("*** Assert error: %d != %d :%s\n", v1, v2, msg);
  abort();
}

[[maybe_unused]] static void test_assert_equal(int32_t v1, int32_t v2, const char* msg = "") {
  if (v1 == v2)
    return;
  printf("*** Assert error: %ld != %ld :%s\n", v1, v2, msg);
  abort();
}

[[maybe_unused]] static void test_assert_equal(uint32_t v1, uint32_t v2, const char* msg = "") {
  if (v1 == v2)
    return;
  printf("*** Assert error: %ld != %ld :%s\n", v1, v2, msg);
  abort();
}

[[maybe_unused]] static void test_conv1d_cfu() {
  const int32_t kernel_length = 8;
  printf("\n==================== Start CFU test (check output) ====================\n");
  cfu_op0(CFU_INITIALIZE, 0, 0);

  // Write values to the input
  cfu_op0(CFU_WRITE_INPUT_BUFFER, 0, 123);
  cfu_op0(CFU_WRITE_INPUT_BUFFER, 1, 255);

  // Read values from the input
  int8_t v0 = cfu_op0(CFU_READ_INPUT_BUFFER, 0, 0);
  int8_t v1 = cfu_op0(CFU_READ_INPUT_BUFFER, 1, 0);

  printf("Write/Read input: v0 = %d (expected 123); v1 = %d (expected -1)\n", v0, v1);

  // Write values to the kernel
  cfu_op0(CFU_WRITE_FILTER_BUFFER, 0, 13);
  cfu_op0(CFU_WRITE_FILTER_BUFFER, 1, -3);

  // Read values from the kernel
  v0 = cfu_op0(CFU_READ_FILTER_BUFFER, 0, 0);
  v1 = cfu_op0(CFU_READ_FILTER_BUFFER, 1, 0);

  printf("Write/Read filter: v0 = %d; (expected 13) v1 = %d (expexted -3) \n", v0, v1);

  // Write input depth for test convolution
  int32_t input_depth = 1;
  cfu_op0(CFU_WRITE_INPUT_DEPTH, 0, input_depth);

  // Write input buffer values (8 * input_depth = 8)
  for (size_t i = 0; i < static_cast<size_t>(kernel_length * input_depth); ++i) {
    cfu_op0(CFU_WRITE_INPUT_BUFFER, i, i);
    cfu_op0(CFU_WRITE_FILTER_BUFFER, i, i);
  }

  // Start computation
  cfu_op0(CFU_START_COMPUTATION, 0, 0);
  // Wait for result
  while (!cfu_op0(CFU_FINISHED, 0, 0)) {
  }
  // Get result
  int32_t acc = cfu_op0(CFU_READ_ACCUMULATOR, 0, 0);
  // 0**2 + 1**2 + ... 7 **2 = 140
  printf("Computation: acc = %ld (expected 140)\n", acc);

  printf("\n==================== End CFU test ====================\n");
}

static void do_tests() {
  test_conv1d_cfu();

  // int8_t epsilon = 20;
  // bool failed    = false;

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_16QAM, pred_simc_3_MIXED_v2_16QAM,
  //          epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_64QAM, pred_simc_3_MIXED_v2_64QAM,
  //          epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_8PSK, pred_simc_3_MIXED_v2_8PSK, epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_B_FM, pred_simc_3_MIXED_v2_B_FM, epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_BPSK, pred_simc_3_MIXED_v2_BPSK, epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_CPFSK, pred_simc_3_MIXED_v2_CPFSK,
  //          epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_DSB_AM, pred_simc_3_MIXED_v2_DSB_AM,
  //          epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_GFSK, pred_simc_3_MIXED_v2_GFSK, epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_PAM4, pred_simc_3_MIXED_v2_PAM4, epsilon);

  // failed = failed ||
  //          perform_one_test(test_data_simc_3_MIXED_v2_QPSK, pred_simc_3_MIXED_v2_QPSK, epsilon);

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_SSB_AM,
  //   pred_simc_3_MIXED_v2_SSB_AM,
  //   epsilon
  // );

  // if (failed) {
  //   printf("FAIL simc_3_MIXED_v2 tests failed\n");
  // } else {
  //   printf("OK   simc_3_MIXED_v2 tests passed\n");
  // }
}

static struct Menu MENU = {
    "Tests for simc_3_MIXED_v2 model",
    "sine",
    {
        MENU_ITEM('g', "Run simc_3_MIXED_v2 tests (check for expected outputs)", do_tests),
        MENU_END,
    },
};

// For integration into menu system
void simc_3_MIXED_v2_menu() {
  simc_3_MIXED_v2_init();
  menu_run(&MENU);
}