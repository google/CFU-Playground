#include "models/simc_2/simc_2.h"

#include <math.h>
#include <stdio.h>

#include "menu.h"
#include "models/simc_2/simc_2_model.h"
#include "models/simc_2/simc_2_test_data.h"
#include "tensorflow/lite/micro/examples/person_detection/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection/person_image_data.h"
#include "playground_util/models_utils.h"
// 
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
static void simc_2_init(void) { 
    tflite_load_model(simc_2_model, simc_2_model_len); 
}

// 

// Run classification, after input has been loaded
static float *simc_2_classify() {
  printf("Running simc_2 model classification\n");
  tflite_classify();

  // Process the inference results.
  float* output = (float*)tflite_get_output();
  return output;
}

#define NUM_CLASSES 11

/* Returns true if failed */
static bool perform_one_test(float* input, float* expected_output, float epsilon) {
  bool failed = false;
  tflite_set_input(input);
  float* output = simc_2_classify();
  for (size_t i = 0; i < NUM_CLASSES; ++i) {
    float y_true = expected_output[i];
    float y_pred = output[i];

    
    float delta = CFU_MAX(y_true, y_pred) - CFU_MIN(y_true, y_pred);
    int* y_true_i32_ptr = (int*)(&y_true);
    int* y_pred_i32_ptr = (int*)(&y_pred);
    if (delta > epsilon) {
      printf(
          "*** simc_2 test failed %d (actual) != %d (pred). "
          "Class=%u\n",
          *y_true_i32_ptr, *y_pred_i32_ptr, i);
    
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
  float epsilon = 0.0005;
  bool failed = false;

  
  failed = failed || perform_one_test(
    test_data_simc_2_16QAM,
    pred_simc_2_16QAM, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_64QAM,
    pred_simc_2_64QAM, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_8PSK,
    pred_simc_2_8PSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_B_FM,
    pred_simc_2_B_FM, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_BPSK,
    pred_simc_2_BPSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_CPFSK,
    pred_simc_2_CPFSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_DSB_AM,
    pred_simc_2_DSB_AM, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_GFSK,
    pred_simc_2_GFSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_PAM4,
    pred_simc_2_PAM4, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_QPSK,
    pred_simc_2_QPSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_2_SSB_AM,
    pred_simc_2_SSB_AM, 
    epsilon
  );    
  

  if (failed) {
    printf("FAIL simc_2 tests failed\n");
  } else {
    printf("OK   simc_2 tests passed\n");
  }
}


static struct Menu MENU = {
    "Tests for simc_2 model",
    "sine",
    {
        MENU_ITEM('g', "Run simc_2 tests (check for expected outputs)", do_tests),
        MENU_END,
    },
};

// For integration into menu system
void simc_2_menu() {
  simc_2_init();
  menu_run(&MENU);
}