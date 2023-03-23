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
static int8_t *simc_3_MIXED_v2_classify() {
  printf("Running simc_3_MIXED_v2 model classification\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = (int8_t*)tflite_get_output();
  return output;
}

#define NUM_CLASSES 11

/* Returns true if failed */
static bool perform_one_test(int8_t* input, int8_t* expected_output, int8_t
epsilon) {
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
      // printf(
      //     "+++ Signal modulation 1 test success %d (actual) != %d (pred).
      // "
      //     "Class=%u\n",
      //     *y_true_u32_ptr, *y_pred_u32_ptr, i);
    }
  }
  return failed;
}


#ifndef CFU_CONV1d_V3_PARAMS
#define CFU_CONV1d_V3_PARAMS

  #define CFU_INITIALIZE 0
  #define CFU_WRITE_TO_INPUT_BUFFER 1
  #define CFU_WRITE_TO_KERNEL_BUFFER 2
  #define CFU_READ_OUTPUT_BUFFER 3
  #define CFU_START_COMPUTATION 4
  #define CFU_READ_INPUT_BUFFER 5
  #define CFU_READ_KERNEL_BUFFER 6
  #define CFU_SET_BIAS 7
#endif // CFU_CONV1d_V3_PARAMS

void printBits(size_t const size, void const * const ptr)
{
    unsigned char *b = (unsigned char*) ptr;
    unsigned char byte;
    int i, j;
    
    for (i = size-1; i >= 0; i--) {
        for (j = 7; j >= 0; j--) {
            byte = (b[i] >> j) & 1;
            printf("%u", byte);
        }
    }
    puts("");
}

/*
  input_uin8t_t4  should be of size 4 (2*4 + 2*4 bytes) 
  kernel_weights_uint8_t4 should be of size 2 (2*4=8 bytes)
*/
static void test_conv1d_cfu_v3(
  uint32_t* input_uin8t_t4,
  uint32_t* input_addresses,
  uint32_t  n_input,

  uint32_t* kernel_weights_uint8_t4, 
  uint32_t* kernel_addresses,
  uint32_t  n_kernel_weights,

  uint8_t bias
) {
  printf("\n==================== Start CFU test (check output) ====================\n");
  cfu_op0(CFU_INITIALIZE, 0, 0);

  printf(">>> Write data to the input buffer\n");
  for (size_t i = 0; i < n_input; ++i) {
    cfu_op0(CFU_WRITE_TO_INPUT_BUFFER, input_addresses[i], input_uin8t_t4[i]);
  }

  printf(">>> Read data from the input buffer\n");
  for (size_t i = 0; i < n_input; ++i) {
    uint32_t read_input_uint8_t4 = cfu_op0(CFU_READ_INPUT_BUFFER, input_addresses[i], 0);
    printf("input_buffer[%ld:%ld] = %lx\n", input_addresses[i], input_addresses[i] + 4, read_input_uint8_t4);
  }

  printf(">>> Write data to kernel weights buffer\n");
  for (size_t i = 0; i < n_kernel_weights; ++i) {
    cfu_op0(CFU_WRITE_TO_KERNEL_BUFFER, kernel_addresses[i], kernel_weights_uint8_t4[i]);
  }

  printf(">>> Read data from kernel buffer\n");
  for (size_t i = 0; i < n_kernel_weights; ++i) {
    uint32_t read_kernel_uint8_t4 = cfu_op0(CFU_READ_KERNEL_BUFFER, kernel_addresses[i], 0);
    printf("kernel_weights_buffer[%ld:%ld] = %lx\n", kernel_addresses[i], kernel_addresses[i] + 4, read_kernel_uint8_t4);
  }

  printf(">>> Set bias\n");
  cfu_op0(CFU_SET_BIAS, bias, 0);

  printf("Start calculations\n");
  cfu_op0(CFU_START_COMPUTATION, 0, 0);

  printf("Read output\n");
  for (size_t output_address = 0; output_address < (n_input - 4 * 2) / 4; ++output_address) {
    uint32_t read_output_uint8_t4 = cfu_op0(CFU_READ_OUTPUT_BUFFER, output_address * 4, 0) ;
    int32_t *read_output = (int32_t*)&read_output_uint8_t4;
    printf("output_buffer[%d] = %lx\n", output_address * 4, *read_output);
    // printBits(sizeof(uint32_t), &read_output_uint8_t4);
  }
  printf("\n==================== End CFU test ====================\n");
}

static void do_tests() {
  #define max_input_channels 128
  #define n_input 16
  #define n_kernel_weights 8
  uint32_t input_uin8t_t4[n_input] = {
    0, 0, 0, 0,       // Left padding
    0x00000007, 0x00000106, 0x00000205, 0x00000304, 0x00000403, 0x00000502, 0x00000601, 0x00000700, 
    // 0x70000000, 0x60100000, 0x50200000, 0x40300000, 0x30400000, 0x20500000, 0x10600000, 0x00700000, 
    0, 0, 0, 0        // Right padding
    };
  uint32_t input_addresses[n_input];
  for (size_t i = 0; i < n_input; ++i) {
    input_addresses[i] = i * max_input_channels;
  }

  uint32_t kernel_weights_uint8_t4[n_kernel_weights] = {
    0x00000102, 0x00000102, 0x00000102, 0x00000102, 0x00000102, 0x00000102, 0x00000102, 0x00000102
    // 0x01010000, 0x01010000, 0x01010000, 0x01010000, 0x01010000, 0x01010000, 0x01010000, 0x01010000
  };
  uint32_t kernel_addresses[n_kernel_weights];
  for (size_t i = 0; i < n_kernel_weights; ++i) {
    kernel_addresses[i] = i * max_input_channels;
  } 

  uint8_t bias = 1;

  test_conv1d_cfu_v3(input_uin8t_t4, input_addresses, n_input,
                     kernel_weights_uint8_t4, kernel_addresses, n_kernel_weights, 
                     bias);

  int8_t epsilon = 20;
  bool failed = false;

  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_16QAM,
    pred_simc_3_MIXED_v2_16QAM,
    epsilon
  );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_64QAM,
  //   pred_simc_3_MIXED_v2_64QAM,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_8PSK,
  //   pred_simc_3_MIXED_v2_8PSK,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_B_FM,
  //   pred_simc_3_MIXED_v2_B_FM,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_BPSK,
  //   pred_simc_3_MIXED_v2_BPSK,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_CPFSK,
  //   pred_simc_3_MIXED_v2_CPFSK,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_DSB_AM,
  //   pred_simc_3_MIXED_v2_DSB_AM,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_GFSK,
  //   pred_simc_3_MIXED_v2_GFSK,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_PAM4,
  //   pred_simc_3_MIXED_v2_PAM4,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_QPSK,
  //   pred_simc_3_MIXED_v2_QPSK,
  //   epsilon
  // );

  // failed = failed || perform_one_test(
  //   test_data_simc_3_MIXED_v2_SSB_AM,
  //   pred_simc_3_MIXED_v2_SSB_AM,
  //   epsilon
  // );

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
        MENU_ITEM('g', "Run simc_3_MIXED_v2 tests (check for expected outputs)",
                  do_tests),
        MENU_END,
    },
};

// For integration into menu system
void simc_3_MIXED_v2_menu() {
  simc_3_MIXED_v2_init();
  menu_run(&MENU);
}