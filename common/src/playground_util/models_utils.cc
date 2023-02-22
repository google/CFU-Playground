#include "models_utils.h"

int8_t quantize(float x) {
  int8_t x_quantized = x / tflite_input_scale() + tflite_input_zero_point();
  return x_quantized;
}

float dequantize(int8_t y_pred_quantized) {
  float y_pred = (y_pred_quantized - tflite_output_zero_point()) * tflite_output_scale();
  return y_pred;
}