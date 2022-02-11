/*
 * Copyright 2021 The CFU-Playground Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
 * Defines tflite functions for evaluating models
 */
#include <stddef.h>
#include <stdint.h>

#ifndef _TFLITE_H
#define _TFLITE_H

#ifndef __cplusplus
#error "tflite.h is for C++ only"
#endif

// Sets up TfLite with a given model
void tflite_load_model(const unsigned char* model_data,
                       unsigned int model_length);
void tflite_set_input_zeros(void);
void tflite_set_input_zeros_float();
void tflite_set_input(const void* data);
void tflite_set_input_unsigned(const unsigned char* data);
void tflite_set_input_float(const float* data);
void tflite_randomize_input(int64_t seed);
void tflite_set_grid_input(void);

// Run classification with data already set into input.
void tflite_classify();

// Obtain the result vector
int8_t* tflite_get_output();
float* tflite_get_output_float();

// The arena
extern uint8_t *tflite_tensor_arena;
#endif  // _TFLITE_H
