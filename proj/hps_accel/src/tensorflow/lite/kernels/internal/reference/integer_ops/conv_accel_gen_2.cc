/*
 * Copyright 2021 The CFU-Playground Authors
 * Copyright 2019 The TensorFlow Authors
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

#include "tensorflow/lite/kernels/internal/reference/integer_ops/conv_accel_gen_2.h"

#include <cstdio>

#include "gateware_constants.h"
#include "hps_cfu.h"
#include "tensorflow/lite/kernels/internal/common.h"

#if GATEWARE_GEN == 2

namespace tflite {
namespace reference_integer_ops {

namespace {

// Loads Post process parameters into the CFU
void LoadPostProcessParameters(int output_depth, const int32_t* bias_data,
                               const int32_t* output_shift,
                               const int32_t* output_multiplier) {
  for (int i = 0; i < output_depth; i++) {
    cfu_set(REG_POST_PROCESS_BIAS, bias_data[i]);
    // Note : shift is stored as a negative number in tflite model
    cfu_set(REG_POST_PROCESS_SHIFT, -output_shift[i]);
    cfu_set(REG_POST_PROCESS_MULTIPLIER, output_multiplier[i]);
  }
}

// Loads filter parameters, correctly split between the two
// stores
void LoadFilterData(const RuntimeShape& filter_shape,
                    const int8_t* filter_data) {
  const int num_filter_words_per_output =
      filter_shape.Dims(1) * filter_shape.Dims(2) * filter_shape.Dims(3) / 4;
  const int num_output_channels = filter_shape.Dims(0);
  const uint32_t* filter_words = reinterpret_cast<const uint32_t*>(filter_data);

  size_t addr_base = 0;
  for (int chan = 0; chan < num_output_channels; chan += 2) {
    for (int store = 0; store < 2; store++) {
      for (int i = 0; i < num_filter_words_per_output; i++) {
        uint32_t data = *filter_words++;
        uint32_t addr = addr_base + i;
        cfu_setx(REG_FILTER_WRITE, (store << 16 | addr), data);
      }
    }
    addr_base += num_filter_words_per_output;
  }
}

};  // namespace

bool CanAccelerateConv4x4(const ConvParams& params,
                          const RuntimeShape& input_shape,
                          const RuntimeShape& filter_shape,
                          const RuntimeShape& output_shape,
                          const int32_t* bias_data) {
  // No padding allowed
  if (params.padding_type != PaddingType::kValid) return false;

  // Must have bias_data and single batch
  if (!bias_data) return false;
  const int batches = MatchingDim(input_shape, 0, output_shape, 0);
  if (batches != 1) return false;

  // Input and output depths must be a multiple of 16
  // NB: We could probably relax output depth to be a multiple of 4
  const int input_depth = input_shape.Dims(3);
  const int output_depth = output_shape.Dims(3);
  // if (input_depth % 16 != 0) return false;
  // if (output_depth % 16 != 0) return false;
  // Currently, only works where input and output depths are exactly 16
  if (input_depth != 16) return false;
  if (output_depth != 16) return false;

  // Must be 4x4
  const int filter_height = filter_shape.Dims(1);
  const int filter_width = filter_shape.Dims(2);
  if (filter_height != 4 || filter_width != 4) return false;

  // Must fit in filter word storag   e
  const int num_filter_words = input_depth * output_depth * 4 * 4 / 4;
  if (num_filter_words > NUM_FILTER_STORES * FILTER_WORDS_PER_STORE)
    return false;

  // Dilation must be 1
  if (params.dilation_height_factor != 1 || params.dilation_width_factor != 1)
    return false;

  // Stride must be 1
  const int stride_width = params.stride_width;
  const int stride_height = params.stride_height;
  if (stride_height != 1 || stride_width != 1) return false;

  return true;
}

// Fixed-point per-channel-quantization convolution reference kernel.
void ConvPerChannel4x4(const ConvParams& params,
                       const int32_t* output_multiplier,
                       const int32_t* output_shift,
                       const RuntimeShape& input_shape,
                       const int8_t* input_data,
                       const RuntimeShape& filter_shape,
                       const int8_t* filter_data,
                       const RuntimeShape& bias_shape, const int32_t* bias_data,
                       const RuntimeShape& output_shape, int8_t* output_data) {
  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  // TODO: handle stride
  // const int stride_width = params.stride_width;
  // const int stride_height = params.stride_height;
  // TODO: handle padding
  // const int pad_width = params.padding_values.width;
  // const int pad_height = params.padding_values.height;
  const int32_t output_offset = params.output_offset;

  // Set min and max value of the output.
  const int32_t output_activation_min = params.quantized_activation_min;
  const int32_t output_activation_max = params.quantized_activation_max;

  // Consistency checks
  TFLITE_DCHECK_LE(output_activation_min, output_activation_max);
  TFLITE_DCHECK_EQ(input_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(filter_shape.DimensionsCount(), 4);
  TFLITE_DCHECK_EQ(output_shape.DimensionsCount(), 4);
  const int input_depth = MatchingDim(input_shape, 3, filter_shape, 3);
  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  TFLITE_DCHECK_EQ(bias_shape.FlatSize(), output_depth);

  // Get dimensions of the tensors.
  const int input_width = input_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  const int filter_size_words = filter_shape.FlatSize() / 4;
  const int num_output_values = output_shape.FlatSize();

  // TODO: Calculate in tranches limited by filter memory size

  // Base address is bank address (4 words per bank) within 256K arena
  uint32_t input_base_addr =
      (reinterpret_cast<uint32_t>(input_data) & 0x3ffff) / 16;

  // Reset to ensure important state is initialized
  cfu_set(REG_ACCELERATOR_RESET, 0);

  // Configure simple values
  cfu_set(REG_INPUT_OFFSET, input_offset);
  cfu_set(REG_NUM_FILTER_WORDS, filter_size_words / 2);
  cfu_set(REG_OUTPUT_OFFSET, output_offset);
  cfu_set(REG_OUTPUT_ACTIVATION_MIN, output_activation_min);
  cfu_set(REG_OUTPUT_ACTIVATION_MAX, output_activation_max);
  cfu_set(REG_INPUT_BASE_ADDR, input_base_addr);
  cfu_set(REG_NUM_PIXELS_X, output_width);
  cfu_set(REG_PIXEL_ADVANCE_X, input_depth / 16);
  cfu_set(REG_PIXEL_ADVANCE_Y, (input_depth / 16) * input_width);
  cfu_set(REG_INPUT_CHANNEL_DEPTH, input_depth);
  cfu_set(REG_OUTPUT_CHANNEL_DEPTH, output_depth);
  cfu_set(REG_NUM_OUTPUT_VALUES, num_output_values);

  LoadPostProcessParameters(output_depth, bias_data, output_shift,
                            output_multiplier);
  LoadFilterData(filter_shape, filter_data);

  // Start Accelerator
  cfu_set(REG_ACCELERATOR_START, 0);

  // Collect data for groups of four pixels
  // TODO: handle number of pixels not being a multiple of 4
  const int num_output_pixels = output_height * output_width;
  const int num_groups = num_output_pixels / 4;
  const int num_words_per_output_pixel = output_depth / 4;
  uint32_t* output_words = reinterpret_cast<uint32_t*>(output_data);
  uint32_t* group_base = output_words;
  for (int group = 0; group < num_groups; group++) {
    uint32_t* g0 = group_base;
    uint32_t* g1 = g0 + num_words_per_output_pixel;
    uint32_t* g2 = g1 + num_words_per_output_pixel;
    uint32_t* g3 = g2 + num_words_per_output_pixel;
    for (int word = 0; word < num_words_per_output_pixel; word++) {
      *g0++ = cfu_get(REG_OUTPUT_WORD);
      *g1++ = cfu_get(REG_OUTPUT_WORD);
      *g2++ = cfu_get(REG_OUTPUT_WORD);
      *g3++ = cfu_get(REG_OUTPUT_WORD);
    }
    group_base += num_words_per_output_pixel * 4;
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
#endif  // GATEWARE_GEN
