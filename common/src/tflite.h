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
#include <stdint.h>

#ifndef _TFLITE_H
#define _TFLITE_H

#ifdef __cplusplus
extern "C" {
#endif

// Runs tflite operation unit tests
void tflite_do_tests();

// Sets up TfLite with a given model
void tflite_load_model(const unsigned char* model_data);
void tflite_set_input_zeros();
void tflite_set_input(const void* data);
void tflite_set_input_unsigned(const unsigned char* data);

// Run classification with data already set into input.
void tflite_classify();

// Obtain the result vector
int8_t* tflite_get_output();

// Obtain the input vector
int8_t* tflite_get_input();

#ifdef __cplusplus
}
#endif
#endif  // _TFLITE_H
