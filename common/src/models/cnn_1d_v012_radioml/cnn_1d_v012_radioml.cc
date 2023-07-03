#include "models/cnn_1d_v012_radioml/cnn_1d_v012_radioml.h"

#include <math.h>
#include <stdio.h>

#include "menu.h"
#include "models/cnn_1d_v012_radioml/cnn_1d_v012_radioml_model.h"
#include "models/cnn_1d_v012_radioml/cnn_1d_v012_radioml_test_data.h"
#include "tensorflow/lite/micro/examples/person_detection/no_person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection/person_image_data.h"
#include "playground_util/models_utils.h"
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
static void cnn_1d_v012_radioml_init(void) { 
    tflite_load_model(cnn_1d_v012_radioml_model, cnn_1d_v012_radioml_model_len); 
}

// Run classification, after input has been loaded
static int8_t *cnn_1d_v012_radioml_classify() {
  printf("Running cnn_1d_v012_radioml model classification\n");
  tflite_classify();

  // Process the inference results.
  int8_t* output = (int8_t*)tflite_get_output();
  return output;
}

#define NUM_CLASSES 11

/* Returns true if failed */
static bool perform_one_test(int8_t* input, int8_t* expected_output, int8_t epsilon) {
  bool failed = false;
  tflite_set_input(input);
  int8_t* output = cnn_1d_v012_radioml_classify();
  for (size_t i = 0; i < NUM_CLASSES; ++i) {
    int8_t y_true = expected_output[i];
    int8_t y_pred = output[i];

    
    int8_t delta = CFU_MAX(y_true, y_pred) - CFU_MIN(y_true, y_pred);
    if (delta > epsilon) {
      printf(
          "*** cnn_1d_v012_radioml test failed %d (actual) != %d (pred). "
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

  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_8PSK,
    pred_cnn_1d_v012_radioml_8PSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_AM_DSB,
    pred_cnn_1d_v012_radioml_AM_DSB, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_AM_SSB,
    pred_cnn_1d_v012_radioml_AM_SSB, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_BPSK,
    pred_cnn_1d_v012_radioml_BPSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_CPFSK,
    pred_cnn_1d_v012_radioml_CPFSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_GFSK,
    pred_cnn_1d_v012_radioml_GFSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_PAM4,
    pred_cnn_1d_v012_radioml_PAM4, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_QAM16,
    pred_cnn_1d_v012_radioml_QAM16, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_QAM64,
    pred_cnn_1d_v012_radioml_QAM64, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_QPSK,
    pred_cnn_1d_v012_radioml_QPSK, 
    epsilon
  );    
  
  failed = failed || perform_one_test(
    test_data_cnn_1d_v012_radioml_WBFM,
    pred_cnn_1d_v012_radioml_WBFM, 
    epsilon
  );    
  

  if (failed) {
    printf("FAIL cnn_1d_v012_radioml tests failed\n");
  } else {
    printf("OK   cnn_1d_v012_radioml tests passed\n");
  }
}


static struct Menu MENU = {
    "Tests for cnn_1d_v012_radioml model",
    "sine",
    {
        MENU_ITEM('g', "Run cnn_1d_v012_radioml tests (check for expected outputs)", do_tests),
        MENU_END,
    },
};

// For integration into menu system
void cnn_1d_v012_radioml_menu() {
  cnn_1d_v012_radioml_init();
  menu_run(&MENU);
}