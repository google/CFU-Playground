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

// Loads four post process parameters into the CFU
void LoadFourPostProcessParameters(int channel_start, const int32_t* bias_data,
                                   const int32_t* output_shift,
                                   const int32_t* output_multiplier) {
  for (int i = channel_start; i < channel_start + 4; i++) {
    cfu_set(REG_POST_PROCESS_BIAS, bias_data[i]);
    // Note : shift is stored as a negative number in tflite model
    cfu_set(REG_POST_PROCESS_SHIFT, -output_shift[i]);
    cfu_set(REG_POST_PROCESS_MULTIPLIER, output_multiplier[i]);
  }
}

// Loads filter parameters, correctly split between the two
// stores
void LoadFourFilterData(int channel_start, const RuntimeShape& filter_shape,
                        const uint32_t* data_base) {
  const int num_filter_words_per_output =
      filter_shape.Dims(1) * filter_shape.Dims(2) * filter_shape.Dims(3) / 4;
  const uint32_t* filter_data =
      data_base + channel_start * num_filter_words_per_output;

  size_t addr_base = 0;
  for (int i = channel_start; i < channel_start + 4; i += 2) {
    for (int store = 0; store < 2; store++) {
      uint32_t addr = addr_base;
      for (int j = 0; j < num_filter_words_per_output; j++) {
        uint32_t data = *filter_data++;
        cfu_setx(REG_FILTER_WRITE, (store << 16 | addr), data);
        addr++;
      }
    }
    addr_base += num_filter_words_per_output;
  }
}

// Collects a single ouput value and optionally places it into memory
inline void CollectValue(uint32_t*& p, int advance, bool write) {
  uint32_t val = cfu_get(REG_OUTPUT_WORD);
  if (write) {
    *p = val;
    p += advance;
  }
}

// Collects output from the accelerator into the output area
// Collects one word per output pixel
void CollectOutput(int channel, uint32_t* output, const int height,
                   const int width, const int depth) {
  const int num_pixels = height * width;
  const int num_words_per_pixel = depth / 4;

  uint32_t* p = output + channel / 4;

  for (int pixel = 0; pixel < num_pixels; pixel += 4) {
    CollectValue(p, num_words_per_pixel, true);
    CollectValue(p, num_words_per_pixel, pixel + 1 < num_pixels);
    CollectValue(p, num_words_per_pixel, pixel + 2 < num_pixels);
    CollectValue(p, num_words_per_pixel, pixel + 3 < num_pixels);
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

  // Input and output depths must be a multiples of 16 and 4
  const int input_depth = input_shape.Dims(3);
  const int output_depth = output_shape.Dims(3);
  if (input_depth % 16 != 0) return false;
  if (output_depth % 4 != 0) return false;

  // Must be 4x4
  const int filter_height = filter_shape.Dims(1);
  const int filter_width = filter_shape.Dims(2);
  if (filter_height != 4 || filter_width != 4) return false;

  // Must fit in filter word storage
  const int filter_values_per_output =
      input_depth * filter_height * filter_width;
  // Calculate 4 output values per tranche
  const int filter_values = 4 * filter_values_per_output;
  // 4 values per word
  const int filter_words = filter_values / 4;
  if (filter_words > NUM_FILTER_STORES * FILTER_WORDS_PER_STORE) return false;

  // Dilation must be 1
  if (params.dilation_height_factor != 1 || params.dilation_width_factor != 1)
    return false;

  // Stride must be 1
  const int stride_width = params.stride_width;
  const int stride_height = params.stride_height;
  if (stride_height != 1 || stride_width != 1) return false;

  return true;
}

// Accelerated Conv2D
void ConvPerChannel4x4(const ConvParams& params,
                       const int32_t* output_multiplier,
                       const int32_t* output_shift,
                       const RuntimeShape& input_shape,
                       const int8_t* input_data,
                       const RuntimeShape& filter_shape,
                       const int8_t* filter_data,
                       const RuntimeShape& bias_shape, const int32_t* bias_data,
                       const RuntimeShape& output_shape, int8_t* output_data) {
  // Calculates in tranches of four channels (one output word)
  const int channels_per_tranche = 4;

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

  // Round up output values to next multiple of 16
  const int num_output_values_per_tranche =
      (output_width * output_height * channels_per_tranche + 15) / 16 * 16;

  // Filter words required to calculate each tranche
  const int filter_words_per_channel =
      filter_shape.Dims(1) * filter_shape.Dims(2) * filter_shape.Dims(3) / 4;
  const int filter_words_per_tranche =
      filter_words_per_channel * channels_per_tranche;

  // Base address is bank address (4 words per bank) within 256K arena
  uint32_t input_base_addr =
      (reinterpret_cast<uint32_t>(input_data) & 0x3ffff) / 16;

  for (int channel = 0; channel < output_depth;
       channel += channels_per_tranche) {
    // Reset to ensure important state is initialized
    cfu_set(REG_ACCELERATOR_RESET, 0);

    // Configure simple values
    cfu_set(REG_INPUT_OFFSET, input_offset);
    cfu_set(REG_NUM_FILTER_WORDS, filter_words_per_tranche / 2);
    cfu_set(REG_OUTPUT_OFFSET, output_offset);
    cfu_set(REG_OUTPUT_ACTIVATION_MIN, output_activation_min);
    cfu_set(REG_OUTPUT_ACTIVATION_MAX, output_activation_max);
    cfu_set(REG_INPUT_BASE_ADDR, input_base_addr);
    cfu_set(REG_NUM_PIXELS_X, output_width);
    cfu_set(REG_PIXEL_ADVANCE_X, input_depth / 16);
    cfu_set(REG_PIXEL_ADVANCE_Y, (input_depth / 16) * input_width);
    cfu_set(REG_INPUT_CHANNEL_DEPTH, input_depth);
    cfu_set(REG_OUTPUT_CHANNEL_DEPTH, channels_per_tranche);
    cfu_set(REG_NUM_OUTPUT_VALUES, num_output_values_per_tranche);

    LoadFourPostProcessParameters(channel, bias_data, output_shift,
                                  output_multiplier);
    LoadFourFilterData(channel, filter_shape,
                       reinterpret_cast<const uint32_t*>(filter_data));

    // Start Accelerator
    cfu_set(REG_ACCELERATOR_START, 0);

    // Collect data
    CollectOutput(channel, reinterpret_cast<uint32_t*>(output_data),
                  output_height, output_width, output_depth);
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
#endif  // GATEWARE_GEN
