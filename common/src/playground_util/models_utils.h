#ifndef MODELS_UTILS_H
#define MODELS_UTILS_H

#include "tflite.h"

int8_t quantize(float x);
float dequantize(int8_t y_pred_quantized);

#endif // MODELS_UTILS_H