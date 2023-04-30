#include "models/simc_3_MIXED_v2/simc_3_MIXED_v2.h"

#include <math.h>
#include <stdio.h>

#include <algorithm>
#include <cassert>

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
    printf("expected[%d] = %d, actual[%d] = %d\n", i, y_true, i, y_pred);

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

namespace {
template <typename IntegerType>
inline IntegerType rounding_divide_by_POT(IntegerType x, int exponent) {
  assert(exponent >= 0);
  assert(exponent <= 31);
  const IntegerType mask      = (1ll << exponent) - 1;
  const IntegerType zero      = 0;
  const IntegerType one       = 1;
  const IntegerType remainder = x & mask;
  const IntegerType threshold = (mask >> 1) + (((x < zero) ? ~0 : 0) & one);
  IntegerType result          = (x >> exponent) + (((remainder > threshold) ? ~0 : 0) & one);
  return result;
}

inline std::int32_t saturating_rounding_doubling_high_mul(std::int32_t a, std::int32_t b) {
  bool overflow = a == b && a == std::numeric_limits<std::int32_t>::min();
  std::int64_t a_64(a);
  std::int64_t b_64(b);
  std::int64_t ab_64        = a_64 * b_64;
  std::int32_t nudge        = ab_64 >= 0 ? (1 << 30) : (1 - (1 << 30));
  std::int32_t ab_x2_high32 = static_cast<std::int32_t>((ab_64 + nudge) / (1ll << 31));
  int32_t result            = overflow ? std::numeric_limits<std::int32_t>::max() : ab_x2_high32;
  // printf("SRDHM: %ld\n", result);
  return result;
}

inline int32_t multiply_by_quant_mult(int32_t x, int32_t quantized_multiplier, int shift) {
  int left_shift  = shift > 0 ? shift : 0;
  int right_shift = shift > 0 ? 0 : -shift;
  int32_t result  = rounding_divide_by_POT(
      saturating_rounding_doubling_high_mul(x * (1 << left_shift), quantized_multiplier),
      right_shift);
  return result;
}
}  // namespace

[[maybe_unused]] static void test_conv1d_cfu() {
  [[maybe_unused]] const int32_t kernel_length = 8;
  int32_t acc;
  printf("\n==================== Start CFU test (check output) ====================\n");

  // // Test quant cfu
  // int32_t output_activation_min = -128;
  // int32_t output_activation_max = 127;
  // int32_t output_offset         = -128;

  // cfu_op0(4, 0, output_activation_min);
  // cfu_op0(5, 0, output_activation_max);
  // cfu_op0(6, 0, output_offset);

  // const size_t accs_size    = 10;
  // int32_t accs[accs_size]   = {-2005, -511, -4625, -8390, 4418, -3837, 8253, -560, -3151, -8283};
  // int32_t biases[accs_size] = {-487, 4205, 3627, -1883, -212, -309, -1601, 3002, 2046, 4152};
  // int32_t output_multipliers[accs_size] = {1848936157, 1106019876, 1245158167, 1182598461,
  //                                          1096005635, 1372768501, 1323832581, 1804904954,
  //                                          1420567106, 2001228717};
  // int32_t output_shifts[accs_size]      = {-7 - 7, -7, -7, -7, -7, -7, -8, -7, -8};
  // // auto accs_size               = sizeof(accs) / sizeof(int32_t);
  // for (size_t i = 0; i < accs_size; ++i) {
  //   int32_t acc = accs[i];
  //   acc += biases[i];
  //   acc = multiply_by_quant_mult(acc, output_multipliers[i], output_shifts[i]);
  //   acc += output_offset;
  //   acc                  = std::max(acc, output_activation_min);
  //   acc                  = std::min(acc, output_activation_max);
  //   int32_t expected_acc = acc;

  //   cfu_op0(1, 0, biases[i]);
  //   cfu_op0(2, 0, output_multipliers[i]);
  //   cfu_op0(3, 0, output_shifts[i]);
  //   acc = cfu_op0(7, 0, accs[i]);
  //   printf("acc = %ld expected( %ld )\n", acc, expected_acc);
  // }

  ////////////////////////////////////

  // // Test Write/REad 4 values at once
  // cfu_op0(CFU_INITIALIZE, 0, 0);

  // for (int i = 0; i < 4; ++i) {
  //   cfu_op0(CFU_WRITE_INPUT_BUFFER, i, static_cast<int8_t>(i + 1));
  // }

  // for (int i = 0; i < 4; ++i) {
  //   int8_t v = cfu_op0(CFU_READ_INPUT_BUFFER, i, 0);
  //   printf("v = %d (expected %d)\n", v, i+1);
  // }

  // // Write input
  // cfu_op0(CFU_WRITE_INPUT_BUFFER, 0, 0x01020304);  // in memory this is 04 03 02 01

  // // Read input
  // for (size_t i = 0; i < 4; ++i) {
  //   int8_t v = cfu_op0(CFU_READ_INPUT_BUFFER, i, 0);
  //   printf("v = %x (expected %d)\n", v, 4 - i);
  // }

  // int8_t arr[]  = {10, 20, 30, 40, 60, 60, 70, 80};
  // int32_t* arr4 = reinterpret_cast<int32_t*>(arr);
  // for (int i = 0; i < 2; ++i) {
  //   cfu_op0(CFU_WRITE_INPUT_BUFFER, i * 4, arr4[i]);
  // }

  // for (int i = 0; i < 8; ++i) {
  //   int8_t v8 = cfu_op0(CFU_READ_INPUT_BUFFER, i, 0);
  //   printf("v8 = %d (expected %d)\n", v8, (i + 1) * 10);
  // }

  ////////////////////

  // Very simple test for conv1d v9
  // Write values to the input
  // cfu_op0(CFU_WRITE_INPUT_BUFFER, 0, 123);
  // cfu_op0(CFU_WRITE_INPUT_BUFFER, 1, 255);

  // // Read values from the input
  // int8_t v0 = cfu_op0(CFU_READ_INPUT_BUFFER, 0, 0);
  // int8_t v1 = cfu_op0(CFU_READ_INPUT_BUFFER, 1, 0);

  // printf("Write/Read input: v0 = %d (expected 123); v1 = %d (expected -1)\n", v0, v1);

  // // Write values to the kernel
  // cfu_op0(CFU_WRITE_FILTER_BUFFER, 0, 13);
  // cfu_op0(CFU_WRITE_FILTER_BUFFER, 1, -3);

  // // Read values from the kernel
  // v0 = cfu_op0(CFU_READ_FILTER_BUFFER, 0, 0);
  // v1 = cfu_op0(CFU_READ_FILTER_BUFFER, 1, 0);

  // printf("Write/Read filter: v0 = %d; (expected 13) v1 = %d (expexted -3) \n", v0, v1);

  // Write input depth for test convolution
  int32_t input_depth = 1;
  cfu_op0(CFU_WRITE_INPUT_DEPTH, 0, input_depth);

  // Write input buffer values (8 * input_depth = 8)
  for (size_t i = 0; i < static_cast<size_t>(kernel_length * input_depth); ++i) {
    cfu_op0(CFU_WRITE_INPUT_BUFFER, i, i + 2);
    cfu_op0(CFU_WRITE_FILTER_BUFFER, i, i);
  }

  // Start computation
  cfu_op0(CFU_START_COMPUTATION, 0, 0);
  // Wait for result
  while (!cfu_op0(CFU_FINISHED, 0, 0)) {
  }
  // Get result
  acc = cfu_op0(CFU_READ_ACCUMULATOR, 0, 0);
  // 0**2 + 1**2 + ... 7 **2 = 140
  printf("Computation: acc = %ld (expected 196)\n", acc);

  ////////////////////

  // cfu_op0(12, 0, 4);
  // cfu_op0(13, 0, 7);
  // cfu_op0(12, 0, 0);
  // cfu_op0(13, 0, 0);
  // acc = cfu_op0(7, 0, 0);
  // printf("Res1 = %ld, expected 196\n", acc);
  // for (int i = 0; i < 16; ++i) {
  //   int v = cfu_op0(14, i, 0);
  //   printf("v = %d, expected: %d\n", v, i % 8);
  // }

  // for (int i = 0; i < 16; ++i) {
  //   cfu_op0(15, i, i % 4);
  //   // cfu_op0(15, i, i % 4);
  //   // cfu_op0(15, i, i % 4);
  //   // cfu_op0(15, i, i % 4);
  // }
  // for (int i = 0; i < 16; ++i) {
  //   int v = cfu_op0(14, i, 0);
  //   printf("v = %d, expected: %d\n", v, i % 4);
  // }
  // cfu_op0(13, 0, 0);
  // acc = cfu_op0(7, 0, 0);
  // printf("Res2 = %ld, expected 28\n", acc);

  printf("\n==================== End CFU test ====================\n");
}

static void do_tests() {
  // test_conv1d_cfu();

  int8_t epsilon = 20;
  bool failed    = false;

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_16QAM, pred_simc_3_MIXED_v2_16QAM, epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_64QAM, pred_simc_3_MIXED_v2_64QAM, epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_8PSK, pred_simc_3_MIXED_v2_8PSK, epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_B_FM, pred_simc_3_MIXED_v2_B_FM, epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_BPSK, pred_simc_3_MIXED_v2_BPSK, epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_CPFSK, pred_simc_3_MIXED_v2_CPFSK,
           epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_DSB_AM, pred_simc_3_MIXED_v2_DSB_AM,
           epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_GFSK, pred_simc_3_MIXED_v2_GFSK, epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_PAM4, pred_simc_3_MIXED_v2_PAM4, epsilon);

  failed = failed ||
           perform_one_test(test_data_simc_3_MIXED_v2_QPSK, pred_simc_3_MIXED_v2_QPSK, epsilon);

  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_SSB_AM,
    pred_simc_3_MIXED_v2_SSB_AM,
    epsilon
  );

  if (failed) {
    printf("FAIL simc_3_MIXED_v2 tests failed\n");
  } else {
    printf("OK   simc_3_MIXED_v2 tests passed\n");
  }
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