/*
 * Copyright 2021 The CFU-Playground Authors
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

#ifndef TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_CONV_ACCEL_GEN_2_H_
#define TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_CONV_ACCEL_GEN_2_H_

#include "tensorflow/lite/kernels/internal/common.h"

#if GATEWARE_GEN == 2
namespace tflite {
namespace reference_integer_ops {
bool CanAccelerateConv4x4(const ConvParams& params,
                          const RuntimeShape& input_shape,
                          const RuntimeShape& filter_shape,
                          const RuntimeShape& output_shape,
                          const int32_t* output_shift,
                          const int32_t* bias_data);

// Accelerated version of ConvPerChannel() specialised for:
// * 4x4 filter size
// * no dilation
void ConvPerChannel4x4(const ConvParams& params,
                       const int32_t* output_multiplier,
                       const int32_t* output_shift,
                       const RuntimeShape& input_shape,
                       const int8_t* input_data,
                       const RuntimeShape& filter_shape,
                       const int8_t* filter_data,
                       const RuntimeShape& bias_shape, const int32_t* bias_data,
                       const RuntimeShape& output_shape, int8_t* output_data);

}  // namespace reference_integer_ops
}  // namespace tflite

#endif  // GATEWARE_GEN

#endif  // TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_CONV_ACCEL_GEN_2_H_
