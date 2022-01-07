/* Copyright 2017 The TensorFlow Authors. All Rights Reserved.

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
#ifndef TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_STRIDED_SLICE_H_
#define TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_STRIDED_SLICE_H_

#include <cstdio>

#include "ruy/profiler/instrumentation.h"  // from @ruy
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/compatibility.h"
#include "tensorflow/lite/kernels/internal/portable_tensor.h"
#include "tensorflow/lite/kernels/internal/strided_slice_logic.h"
#include "tensorflow/lite/kernels/internal/types.h"

namespace tflite {

namespace reference_ops {

template <typename T>
inline void StridedSlice(const tflite::StridedSliceParams& op_params,
                         const RuntimeShape& unextended_input_shape,
                         const RuntimeShape& unextended_output_shape,
                         SequentialTensorWriter<T>* writer) {
  using strided_slice::LoopCondition;
  using strided_slice::StartForAxis;
  using strided_slice::StopForAxis;

  ruy::profiler::ScopeLabel label("StridedSlice");

  // Note that the output_shape is not used herein.
  tflite::StridedSliceParams params_copy = op_params;

  TFLITE_DCHECK_LE(unextended_input_shape.DimensionsCount(), 5);
  TFLITE_DCHECK_LE(unextended_output_shape.DimensionsCount(), 5);
  const RuntimeShape input_shape =
      RuntimeShape::ExtendedShape(5, unextended_input_shape);
  const RuntimeShape output_shape =
      RuntimeShape::ExtendedShape(5, unextended_output_shape);

  // Reverse and pad to 5 dimensions because that is what the runtime code
  // requires (ie. all shapes must be 5D and are given backwards).
  strided_slice::StridedSlicePadIndices(&params_copy, 5);

  const int start_0 = StartForAxis(params_copy, input_shape, 0);
  const int stop_0 = StopForAxis(params_copy, input_shape, 0, start_0);
  const int start_1 = StartForAxis(params_copy, input_shape, 1);
  const int stop_1 = StopForAxis(params_copy, input_shape, 1, start_1);
  const int start_2 = StartForAxis(params_copy, input_shape, 2);
  const int stop_2 = StopForAxis(params_copy, input_shape, 2, start_2);
  const int start_3 = StartForAxis(params_copy, input_shape, 3);
  const int stop_3 = StopForAxis(params_copy, input_shape, 3, start_3);
  const int start_4 = StartForAxis(params_copy, input_shape, 4);
  const int stop_4 = StopForAxis(params_copy, input_shape, 4, start_4);

  for (int offset_0 = start_0 * input_shape.Dims(1),
           end_0 = stop_0 * input_shape.Dims(1),
           step_0 = params_copy.strides[0] * input_shape.Dims(1);
       !LoopCondition(offset_0, end_0, params_copy.strides[0]);
       offset_0 += step_0) {
    for (int offset_1 = (offset_0 + start_1) * input_shape.Dims(2),
             end_1 = (offset_0 + stop_1) * input_shape.Dims(2),
             step_1 = params_copy.strides[1] * input_shape.Dims(2);
         !LoopCondition(offset_1, end_1, params_copy.strides[1]);
         offset_1 += step_1) {
      for (int offset_2 = (offset_1 + start_2) * input_shape.Dims(3),
               end_2 = (offset_1 + stop_2) * input_shape.Dims(3),
               step_2 = params_copy.strides[2] * input_shape.Dims(3);
           !LoopCondition(offset_2, end_2, params_copy.strides[2]);
           offset_2 += step_2) {
        for (int offset_3 = (offset_2 + start_3) * input_shape.Dims(4),
                 end_3 = (offset_2 + stop_3) * input_shape.Dims(4),
                 step_3 = params_copy.strides[3] * input_shape.Dims(4);
             !LoopCondition(offset_3, end_3, params_copy.strides[3]);
             offset_3 += step_3) {
          for (int offset_4 = offset_3 + start_4, end_4 = offset_3 + stop_4;
               !LoopCondition(offset_4, end_4, params_copy.strides[4]);
               offset_4 += params_copy.strides[4]) {
            writer->Write(offset_4);
          }
        }
      }
    }
  }
}

inline void StridedSlice(const tflite::StridedSliceParams& op_params,
                         const RuntimeShape& unextended_input_shape,
                         const int8_t* input_data,
                         const RuntimeShape& unextended_output_shape,
                         int8_t* output_data) {
  // start_indices_count,
  // start_indices[0], start_indices[1], start_indices[2], start_indices[3],
  // stop_indices_count,
  // stop_indices[0], stop_indices[1], stop_indices[2], stop_indices[3],
  // strides_count,
  // strides[0], strides[1], strides[2], strides[3],
  // begin_mask, ellipsis_mask, end_mask, new_axis_mask, shrink_axis_mask,
  // input_shape[0], input_shape[1], input_shape[2], input_shape[3],
  // output_shape[0], output_shape[1], output_shape[2], output_shape[3],
#ifdef SHOW_STRIDED_SLICE_PARAMS
  printf("\n");
  printf("%d, %ld, %ld, %ld, %ld, ", op_params.start_indices_count,
         op_params.start_indices[0], op_params.start_indices[1],
         op_params.start_indices[2], op_params.start_indices[3]);
  printf("%d, %ld, %ld, %ld, %ld, ", op_params.stop_indices_count,
         op_params.stop_indices[0], op_params.stop_indices[1],
         op_params.stop_indices[2], op_params.stop_indices[3]);
  printf("%d, %ld, %ld, %ld, %ld, ", op_params.strides_count,
         op_params.strides[0], op_params.strides[1], op_params.strides[2],
         op_params.strides[3]);
  printf("%d, %d, %d, %d, %d, ", op_params.begin_mask, op_params.ellipsis_mask,
         op_params.end_mask, op_params.new_axis_mask,
         op_params.shrink_axis_mask);
  printf("%ld, %ld, %ld, %ld, ", unextended_input_shape.Dims(0),
         unextended_input_shape.Dims(1), unextended_input_shape.Dims(2),
         unextended_input_shape.Dims(3));
  printf("%ld, %ld, %ld, %ld, ", unextended_output_shape.Dims(0),
         unextended_output_shape.Dims(1), unextended_output_shape.Dims(2),
         unextended_output_shape.Dims(3));
  printf("\n");
#endif

#ifdef ACCEL_STRIDED_SLICE
  if (op_params.strides_count == 4 &&  //
      op_params.strides[0] == 1 && op_params.strides[1] == 1 &&
      op_params.strides[2] == 1 && op_params.strides[3] == 1 &&
      op_params.start_indices_count == 4 &&  //
      op_params.start_indices[0] == 0 && op_params.start_indices[2] == 0 &&
      op_params.start_indices[3] == 0 && op_params.stop_indices_count == 4 &&
      op_params.stop_indices[0] == 0 && op_params.stop_indices[2] == 0 &&
      op_params.stop_indices[3] == 0 &&
      unextended_input_shape.DimensionsCount() == 4 &&
      unextended_input_shape.Dims(0) == 1) {
    int width = unextended_input_shape.Dims(2);
    int depth = unextended_input_shape.Dims(3);
    int start_offset = op_params.start_indices[1] * depth * width;
    int stop_offset = op_params.stop_indices[1] * depth * width;

    if (start_offset % 4 == 0 && stop_offset % 4 == 0) {
      const uint32_t* start_word =
          reinterpret_cast<const uint32_t*>(input_data + start_offset);
      const uint32_t* stop_word =
          reinterpret_cast<const uint32_t*>(input_data + stop_offset);
      uint32_t* output_words = reinterpret_cast<uint32_t*>(output_data);
      // Copy 4 words at a time
      const uint32_t* p = start_word;
      while (p < stop_word - 3) {
        *output_words++ = *p++;
        *output_words++ = *p++;
        *output_words++ = *p++;
        *output_words++ = *p++;
      }
      // Residuals
      while (p < stop_word) {
        *output_words++ = *p++;
      }
      return;
    }
  }
#endif

  SequentialTensorWriter<int8_t> writer(input_data, output_data);
  StridedSlice<int8_t>(op_params, unextended_input_shape,
                       unextended_output_shape, &writer);
}

template <typename T>
inline void StridedSlice(const tflite::StridedSliceParams& op_params,
                         const RuntimeShape& unextended_input_shape,
                         const T* input_data,
                         const RuntimeShape& unextended_output_shape,
                         T* output_data) {
  SequentialTensorWriter<T> writer(input_data, output_data);
  StridedSlice<T>(op_params, unextended_input_shape, unextended_output_shape,
                  &writer);
}

template <typename T>
inline void StridedSlice(const tflite::StridedSliceParams& op_params,
                         const RuntimeShape& unextended_input_shape,
                         const TfLiteTensor* input,
                         const RuntimeShape& unextended_output_shape,
                         TfLiteTensor* output) {
  SequentialTensorWriter<T> writer(input, output);
  StridedSlice<T>(op_params, unextended_input_shape, unextended_output_shape,
                  &writer);
}

}  // namespace reference_ops
}  // namespace tflite

#endif  // TENSORFLOW_LITE_KERNELS_INTERNAL_REFERENCE_STRIDED_SLICE_H_
