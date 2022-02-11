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
#ifndef _PRINT_PARAMS_H
#define _PRINT_PARAMS_H
#include "tensorflow/lite/kernels/internal/types.h"

void print_conv_params(const tflite::ConvParams& params,
                       const tflite::RuntimeShape& input_shape,
                       const tflite::RuntimeShape& filter_shape,
                       const tflite::RuntimeShape& output_shape);

void print_depthwise_params(const tflite::DepthwiseParams& params,
                            const tflite::RuntimeShape& input_shape,
                            const tflite::RuntimeShape& filter_shape,
                            const tflite::RuntimeShape& output_shape);

void print_arithmetic_params(const char* op_name,
                             const tflite::ArithmeticParams& params,
                             const tflite::RuntimeShape& input1_shape,
                             const tflite::RuntimeShape& input2_shape,
                             const tflite::RuntimeShape& output_shape);

void print_int32_array(const int32_t* data, size_t count);

#endif  // _PRINT_PARAMS_H
