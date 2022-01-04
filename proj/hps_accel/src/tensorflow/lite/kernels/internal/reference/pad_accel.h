/*
 * Copyright 2022 The CFU-Playground Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_ACCEL_PAD_H_
#define TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_ACCEL_PAD_H_

#include "tensorflow/lite/kernels/internal/types.h"

namespace tflite {
namespace reference_ops {

// Determine whether operation is suitable for acceleration
bool CanAcceleratePad(const tflite::PadParams& op_params,
                      const RuntimeShape& input_shape, const int8_t* input_data,
                      const int8_t* pad_value_ptr,
                      const RuntimeShape& output_shape);

// Accelerate the operation
void AcceleratePad(const tflite::PadParams& op_params,
                   const RuntimeShape& input_shape, const int8_t* input_data,
                   const int8_t* pad_value_ptr,
                   const RuntimeShape& output_shape, int8_t* output_data);

}  // namespace reference_ops
}  // namespace tflite

#endif  // TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_ACCEL_PAD_H_
