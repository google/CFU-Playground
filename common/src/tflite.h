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

void tflite_do_tests();
void tflite_init();
void tflite_load_model(unsigned char *model_data);

void initTfLite();
void load_zeros();
void classify(int8_t *person_score, int8_t *no_person_score);

#ifdef __cplusplus
}
#endif
#endif // _TFLITE_H
