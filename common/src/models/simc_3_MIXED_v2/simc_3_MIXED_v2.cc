#include "models/simc_3_MIXED_v2/simc_3_MIXED_v2.h"

#include <math.h>
#include <stdio.h>

#include "menu.h"
#include "models/simc_3_MIXED_v2/simc_3_MIXED_v2_model.h"
#include "models/simc_3_MIXED_v2/simc_3_MIXED_v2_test_data.h"
#include "tensorflow/lite/micro/examples/person_detection/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection/person_image_data.h"
#include "playground_util/models_utils.h"
// 
// #include "playground_util/models_utils.h"
// 
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

// 
// float dequantized_output[11];
// 

// Run classification, after input has been loaded
static int8_t *simc_3_MIXED_v2_classify() {
  printf("Running simc_3_MIXED_v2 model classification\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = (int8_t*)tflite_get_output();
  return output;
}

#define NUM_CLASSES 11

/*
  https://five-embeddev.com/riscv-isa-manual/latest/csr.html

  RISC-V manual: 
  3.1.14 Machine Timer Registers (mtime and mtimecmp)
*/
// static inline uint64_t perf_get_mtime() {
//   uint32_t counts = 0;
//   uint32_t zero = 0;
//   asm volatile(
//       "li %0, 0xc01;"
//       "lw %1, 0(%0);"
//       : "+r"(zero), "=r"(counts)
//       :);
//   return (uint64_t) counts;
// }
// static inline uint64_t perf_get_mtime() {
//   uint32_t time_low = 0;
//   uint32_t time_high = 0;
//   uint32_t time_high_2 = 0;
//   asm volatile(
//       "read%=:"
//       "  csrr %0, 0xc80;"     // Read `timeh`.
//       "  csrr %1, 0xc00;"      // Read `time`.
//       "  csrr %2, 0xc80;"     // Read `timeh` again.
//       "  bne  %0, %2, read%=;"  // Try again if `time` overflowed before
//                                 // reading `timeh`.
//       : "+r"(time_high), "=r"(time_low), "+r"(time_high_2)
//       :);
//   return (uint64_t) time_high << 32 | time_low;
// }



/* Returns true if failed */
static bool perform_one_test(int8_t* input, int8_t* expected_output, int8_t epsilon) {
  bool failed = false;
  tflite_set_input(input);
  int8_t* output = simc_3_MIXED_v2_classify();
  for (size_t i = 0; i < NUM_CLASSES; ++i) {
    int8_t y_true = expected_output[i];
    int8_t y_pred = output[i];

    
    int8_t delta = CFU_MAX(y_true, y_pred) - CFU_MIN(y_true, y_pred);
    if (delta > epsilon) {
      printf(
          "*** simc_3_MIXED_v2 test failed %d (actual) != %d (pred). "
          "Class=%u\n",
          y_true, y_pred, i);
    
      failed = true;
    } else {
      // printf(
      //     "+++ Signal modulation 1 test success %d (actual) != %d (pred). "
      //     "Class=%u\n",
      //     *y_true_u32_ptr, *y_pred_u32_ptr, i);
    }
  }
  return failed;
}

static void do_tests() {
  int8_t epsilon = 20;
  bool failed = false;

  // uint64_t before = perf_get_mtime();
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_16QAM,
    pred_simc_3_MIXED_v2_16QAM, 
    epsilon
  );    
  // uint64_t after = perf_get_mtime();
  // printf("after - before: %llu\n", (after - before));
  
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
        MENU_ITEM('g', "Run simc_3_MIXED_v2 tests (check for expected outputs)", do_tests),
        MENU_END,
    },
};

// For integration into menu system
void simc_3_MIXED_v2_menu() {
  simc_3_MIXED_v2_init();
  menu_run(&MENU);
}