/* Copyright 2018 The TensorFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/
#ifndef TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_POOLING_H_
#define TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_POOLING_H_

#include <cstdio>
#include <limits>

#include "playground_util/murmurhash.h"
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/reference/integer_ops/pooling_accel.h"

namespace tflite {
namespace reference_integer_ops {

inline bool AveragePool(const PoolParams& params,
                        const RuntimeShape& input_shape,
                        const int8_t* input_data,
                        const RuntimeShape& output_shape, int8_t* output_data) {
  TFLITE_DCHECK_LE(params.quantized_activation_min,
                   params.quantized_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int depth = MatchingDim(input_shape, 3, output_shape, 3);
  const int input_height = input_shape.Dims(1);
  const int input_width = input_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  const int stride_height = params.stride_height;
  const int stride_width = params.stride_width;
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      for (int out_x = 0; out_x < output_width; ++out_x) {
        for (int channel = 0; channel < depth; ++channel) {
          const int in_x_origin =
              (out_x * stride_width) - params.padding_values.width;
          const int in_y_origin =
              (out_y * stride_height) - params.padding_values.height;
          // Compute the boundaries of the filter region clamped so as to
          // ensure that the filter window fits in the input array.
          const int filter_x_start = std::max(0, -in_x_origin);
          const int filter_x_end =
              std::min(params.filter_width, input_width - in_x_origin);
          const int filter_y_start = std::max(0, -in_y_origin);
          const int filter_y_end =
              std::min(params.filter_height, input_height - in_y_origin);
          int32_t acc = 0;
          int filter_count = 0;
          for (int filter_y = filter_y_start; filter_y < filter_y_end;
               ++filter_y) {
            for (int filter_x = filter_x_start; filter_x < filter_x_end;
                 ++filter_x) {
              const int in_x = in_x_origin + filter_x;
              const int in_y = in_y_origin + filter_y;
              acc +=
                  input_data[Offset(input_shape, batch, in_y, in_x, channel)];
              filter_count++;
            }
          }
          if (filter_count == 0) return false;
          // Round to the closest integer value.
          acc = acc > 0 ? (acc + filter_count / 2) / filter_count
                        : (acc - filter_count / 2) / filter_count;
          acc = std::max(acc, params.quantized_activation_min);
          acc = std::min(acc, params.quantized_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, channel)] =
              static_cast<int8_t>(acc);
        }
      }
    }
  }
  return true;
}

inline void UnacceleratedMaxPool(const PoolParams& params,
                                 const RuntimeShape& input_shape,
                                 const int8_t* input_data,
                                 const RuntimeShape& output_shape,
                                 int8_t* output_data) {
  TFLITE_DCHECK_LE(params.quantized_activation_min,
                   params.quantized_activation_max);
  TFLITE_DCHECK_GE(params.quantized_activation_min,
                   std::numeric_limits<int8_t>::min());
  TFLITE_DCHECK_LE(params.quantized_activation_max,
                   std::numeric_limits<int8_t>::max());
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int depth = MatchingDim(input_shape, 3, output_shape, 3);
  const int input_height = input_shape.Dims(1);
  const int input_width = input_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  const int stride_height = params.stride_height;
  const int stride_width = params.stride_width;
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      for (int out_x = 0; out_x < output_width; ++out_x) {
        for (int channel = 0; channel < depth; ++channel) {
          const int in_x_origin =
              (out_x * stride_width) - params.padding_values.width;
          const int in_y_origin =
              (out_y * stride_height) - params.padding_values.height;
          // Compute the boundaries of the filter region clamped so as to
          // ensure that the filter window fits in the input array.
          const int filter_x_start = std::max(0, -in_x_origin);
          const int filter_x_end =
              std::min(params.filter_width, input_width - in_x_origin);
          const int filter_y_start = std::max(0, -in_y_origin);
          const int filter_y_end =
              std::min(params.filter_height, input_height - in_y_origin);
          int8_t max = std::numeric_limits<int8_t>::lowest();
          for (int filter_y = filter_y_start; filter_y < filter_y_end;
               ++filter_y) {
            for (int filter_x = filter_x_start; filter_x < filter_x_end;
                 ++filter_x) {
              const int in_x = in_x_origin + filter_x;
              const int in_y = in_y_origin + filter_y;
              max = std::max(
                  max,
                  input_data[Offset(input_shape, batch, in_y, in_x, channel)]);
            }
          }
          max = std::max<int8_t>(max, params.quantized_activation_min);
          max = std::min<int8_t>(max, params.quantized_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, channel)] =
              static_cast<int8_t>(max);
        }
      }
    }
  }
}

inline void MaxPool(const PoolParams& params, const RuntimeShape& input_shape,
                    const int8_t* input_data, const RuntimeShape& output_shape,
                    int8_t* output_data) {
#if SHOW_MAX_POOL_PARAMS
  // padding_width, padding_height,
  // stride_width, stride_height, filter_height, filter_width,
  // quantized_activation_min, quantized_activation_max,
  // input_shape[0], input_shape[1], input_shape[2], input_shape[3],
  // output_shape[0], output_shape[1], output_shape[2], output_shape[3]
  printf("\n");
  const auto& padding = params.padding_values;
  printf("%d, %d, ", padding.width, padding.height);
  printf("%d, %d, %d, %d, ", params.stride_height, params.stride_width,
         params.filter_height, params.filter_width);
  printf("%ld, %ld, ", params.quantized_activation_min,
         params.quantized_activation_max);
  printf("%ld, %ld, %ld, %ld, ", input_shape.Dims(0), input_shape.Dims(1),
         input_shape.Dims(2), input_shape.Dims(3));
  printf("%ld, %ld, %ld, %ld, ", output_shape.Dims(0), output_shape.Dims(1),
         output_shape.Dims(2), output_shape.Dims(3));

  printf("\n");
#endif

  bool accelerated = false;

#ifdef ACCEL_MAX_POOL
#if GATEWARE_GEN != 2
#error MAX_POOL op requires gateware gen 2
#endif
  accelerated = CanAccelerateMaxPool(params, input_shape, output_shape);
  if (accelerated) {
    AccelerateMaxPool(params, input_shape, input_data, output_shape,
                      output_data);
  }
#endif
  if (!accelerated) {
    UnacceleratedMaxPool(params, input_shape, input_data, output_shape,
                         output_data);
  }

#ifdef SHOW_POOL_HASHES
  static int hash_layer = 0;
  int32_t input_hash = murmurhash3_32(reinterpret_cast<const uint8_t*>(input_data),
                                      input_shape.FlatSize());
  int32_t output_hash = murmurhash3_32(reinterpret_cast<const uint8_t*>(output_data),
                                       output_shape.FlatSize());
  printf("%3d, %08lx, %08lx\n", hash_layer, input_hash, output_hash);
  hash_layer++;
#endif
}

inline bool AveragePool(const PoolParams& params,
                        const RuntimeShape& input_shape,
                        const int16_t* input_data,
                        const RuntimeShape& output_shape,
                        int16_t* output_data) {
  TFLITE_DCHECK_LE(params.quantized_activation_min,
                   params.quantized_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int depth = MatchingDim(input_shape, 3, output_shape, 3);
  const int input_height = input_shape.Dims(1);
  const int input_width = input_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  const int stride_height = params.stride_height;
  const int stride_width = params.stride_width;
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      for (int out_x = 0; out_x < output_width; ++out_x) {
        for (int channel = 0; channel < depth; ++channel) {
          const int in_x_origin =
              (out_x * stride_width) - params.padding_values.width;
          const int in_y_origin =
              (out_y * stride_height) - params.padding_values.height;
          // Compute the boundaries of the filter region clamped so as to
          // ensure that the filter window fits in the input array.
          const int filter_x_start = std::max(0, -in_x_origin);
          const int filter_x_end =
              std::min(params.filter_width, input_width - in_x_origin);
          const int filter_y_start = std::max(0, -in_y_origin);
          const int filter_y_end =
              std::min(params.filter_height, input_height - in_y_origin);
          int32_t acc = 0;
          int filter_count = 0;
          for (int filter_y = filter_y_start; filter_y < filter_y_end;
               ++filter_y) {
            for (int filter_x = filter_x_start; filter_x < filter_x_end;
                 ++filter_x) {
              const int in_x = in_x_origin + filter_x;
              const int in_y = in_y_origin + filter_y;
              acc +=
                  input_data[Offset(input_shape, batch, in_y, in_x, channel)];
              filter_count++;
            }
          }
          if (filter_count == 0) return false;
          // Round to the closest integer value.
          acc = acc > 0 ? (acc + filter_count / 2) / filter_count
                        : (acc - filter_count / 2) / filter_count;
          acc = std::max(acc, params.quantized_activation_min);
          acc = std::min(acc, params.quantized_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, channel)] =
              static_cast<int16_t>(acc);
        }
      }
    }
  }
  return true;
}

inline void MaxPool(const PoolParams& params, const RuntimeShape& input_shape,
                    const int16_t* input_data, const RuntimeShape& output_shape,
                    int16_t* output_data) {
  TFLITE_DCHECK_LE(params.quantized_activation_min,
                   params.quantized_activation_max);
  TFLITE_DCHECK_GE(params.quantized_activation_min,
                   std::numeric_limits<int16_t>::min());
  TFLITE_DCHECK_LE(params.quantized_activation_max,
                   std::numeric_limits<int16_t>::max());
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  const int depth = MatchingDim(input_shape, 3, output_shape, 3);
  const int input_height = input_shape.Dims(1);
  const int input_width = input_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  const int stride_height = params.stride_height;
  const int stride_width = params.stride_width;
  for (int batch = 0; batch < batches; ++batch) {
    for (int out_y = 0; out_y < output_height; ++out_y) {
      for (int out_x = 0; out_x < output_width; ++out_x) {
        for (int channel = 0; channel < depth; ++channel) {
          const int in_x_origin =
              (out_x * stride_width) - params.padding_values.width;
          const int in_y_origin =
              (out_y * stride_height) - params.padding_values.height;
          // Compute the boundaries of the filter region clamped so as to
          // ensure that the filter window fits in the input array.
          const int filter_x_start = std::max(0, -in_x_origin);
          const int filter_x_end =
              std::min(params.filter_width, input_width - in_x_origin);
          const int filter_y_start = std::max(0, -in_y_origin);
          const int filter_y_end =
              std::min(params.filter_height, input_height - in_y_origin);
          int16_t max = std::numeric_limits<int16_t>::lowest();
          for (int filter_y = filter_y_start; filter_y < filter_y_end;
               ++filter_y) {
            for (int filter_x = filter_x_start; filter_x < filter_x_end;
                 ++filter_x) {
              const int in_x = in_x_origin + filter_x;
              const int in_y = in_y_origin + filter_y;
              max = std::max(
                  max,
                  input_data[Offset(input_shape, batch, in_y, in_x, channel)]);
            }
          }
          max = std::max<int16_t>(max, params.quantized_activation_min);
          max = std::min<int16_t>(max, params.quantized_activation_max);
          output_data[Offset(output_shape, batch, out_y, out_x, channel)] =
              static_cast<int16_t>(max);
        }
      }
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite

#endif  // TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_INTEGER_OPS_POOLING_H_
