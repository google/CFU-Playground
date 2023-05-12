#include "models/simc_3_MIXED_v2_no_quant/simc_3_MIXED_v2_no_quant.h"

#include <math.h>
#include <stdio.h>

#include "menu.h"
#include "models/simc_3_MIXED_v2_no_quant/simc_3_MIXED_v2_no_quant_model.h"
#include "models/simc_3_MIXED_v2_no_quant/simc_3_MIXED_v2_no_quant_test_data.h"
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
static void simc_3_MIXED_v2_no_quant_init(void) { 
    tflite_load_model(simc_3_MIXED_v2_no_quant_model, simc_3_MIXED_v2_no_quant_model_len); 
}

// 

// Run classification, after input has been loaded
static float *simc_3_MIXED_v2_no_quant_classify() {
  printf("Running simc_3_MIXED_v2_no_quant model classification\n");
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
  float* output = simc_3_MIXED_v2_no_quant_classify();
  for (size_t i = 0; i < NUM_CLASSES; ++i) {
    float y_true = expected_output[i];
    float y_pred = output[i];

    
    float delta = CFU_MAX(y_true, y_pred) - CFU_MIN(y_true, y_pred);
    int* y_true_i32_ptr = (int*)(&y_true);
    int* y_pred_i32_ptr = (int*)(&y_pred);
    if (delta > epsilon) {
      printf(
          "*** simc_3_MIXED_v2_no_quant test failed %d (actual) != %d (pred). "
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
  float epsilon = 20;
  bool failed = false;

  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_16QAM,
    pred_simc_3_MIXED_v2_no_quant_16QAM, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_64QAM,
    pred_simc_3_MIXED_v2_no_quant_64QAM, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_8PSK,
    pred_simc_3_MIXED_v2_no_quant_8PSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_B_FM,
    pred_simc_3_MIXED_v2_no_quant_B_FM, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_BPSK,
    pred_simc_3_MIXED_v2_no_quant_BPSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_CPFSK,
    pred_simc_3_MIXED_v2_no_quant_CPFSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_DSB_AM,
    pred_simc_3_MIXED_v2_no_quant_DSB_AM, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_GFSK,
    pred_simc_3_MIXED_v2_no_quant_GFSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_PAM4,
    pred_simc_3_MIXED_v2_no_quant_PAM4, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_QPSK,
    pred_simc_3_MIXED_v2_no_quant_QPSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_simc_3_MIXED_v2_no_quant_SSB_AM,
    pred_simc_3_MIXED_v2_no_quant_SSB_AM, 
    epsilon
  );    
  

  if (failed) {
    printf("FAIL simc_3_MIXED_v2_no_quant tests failed\n");
  } else {
    printf("OK   simc_3_MIXED_v2_no_quant tests passed\n");
  }
}


static struct Menu MENU = {
    "Tests for simc_3_MIXED_v2_no_quant model",
    "sine",
    {
        MENU_ITEM('g', "Run simc_3_MIXED_v2_no_quant tests (check for expected outputs)", do_tests),
        MENU_END,
    },
};

// For integration into menu system
void simc_3_MIXED_v2_no_quant_menu() {
  simc_3_MIXED_v2_no_quant_init();
  menu_run(&MENU);
}