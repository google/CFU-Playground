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

#include <algorithm>
#include <cstdio>

#include "gateware_constants.h"
#include "hps_cfu.h"
#include "tensorflow/lite/kernels/internal/common.h"

#if GATEWARE_GEN == 2

namespace tflite {
namespace reference_integer_ops {

namespace {

// Loads process parameters into the CFU
void LoadPostProcessParameters(int channel_start, int num_channels,
                               const int32_t* bias_data,
                               const int32_t* output_shift,
                               const int32_t* output_multiplier) {
  for (int i = channel_start; i < channel_start + num_channels; i++) {
    cfu_set(REG_POST_PROCESS_BIAS, bias_data[i]);
    // Note : shift is stored as a negative number in tflite model
    cfu_set(REG_POST_PROCESS_SHIFT, -output_shift[i]);
    cfu_set(REG_POST_PROCESS_MULTIPLIER, output_multiplier[i]);
  }
}

// Loads filter parameters, correctly split between the two stores
void LoadFilterData(int channel_start, int num_channels,
                    const RuntimeShape& filter_shape,
                    const uint32_t* data_base) {
  const int num_filter_words_per_output =
      filter_shape.Dims(1) * filter_shape.Dims(2) * filter_shape.Dims(3) / 4;
  const uint32_t* filter_data =
      data_base + channel_start * num_filter_words_per_output;

  size_t addr_base = 0;
  for (int i = channel_start; i < channel_start + num_channels; i += 2) {
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
  if (write) *p = val;
  p += advance;
}

// Collects output from the accelerator into the output area for groups of four
// pixels. Collects num_channels of data per pixel.
void CollectOutput(const int start_channel, const int num_channels,
                   uint32_t* output, const int num_pixels, const int depth) {
  const int num_words_per_pixel = depth / 4;

  // Find first output location
  uint32_t* p_base = output + start_channel / 4;
  for (int pixel = 0; pixel < num_pixels; pixel += 4) {
    for (int c = 0; c < num_channels; c += 4) {
      uint32_t* p = p_base + c / 4;
      CollectValue(p, num_words_per_pixel, true);
      CollectValue(p, num_words_per_pixel, pixel + 1 < num_pixels);
      CollectValue(p, num_words_per_pixel, pixel + 2 < num_pixels);
      CollectValue(p, num_words_per_pixel, pixel + 3 < num_pixels);
    }
    p_base += num_words_per_pixel * 4;
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

  const int stride_width = params.stride_width;
  const int stride_height = params.stride_height;
  if (input_depth == 1) {
    // For input layers, stride must be two
    if (stride_height != 2 || stride_width != 2) return false;
    // Input and output width are fixed
    if (input_shape.Dims(2) != 322 || output_shape.Dims(2) != 160) return false;
  } else {
    // For all other layers, stride must be 1
    if (stride_height != 1 || stride_width != 1) return false;
  }

  return true;
}

// Accelerated Conv2D
// Assumes CanAccelerateConv4x4() returned true with these input parameters
void ConvPerChannel4x4(const ConvParams& params,
                       const int32_t* output_multiplier,
                       const int32_t* output_shift,
                       const RuntimeShape& input_shape,
                       const int8_t* input_data,
                       const RuntimeShape& filter_shape,
                       const int8_t* filter_data,
                       const RuntimeShape& bias_shape, const int32_t* bias_data,
                       const RuntimeShape& output_shape, int8_t* output_data) {
  const int input_depth = input_shape.Dims(3);
  const int output_depth = output_shape.Dims(3);

  // Get dimensions of the tensors.
  const int input_width = input_shape.Dims(2);
  const int output_height = output_shape.Dims(1);
  const int output_width = output_shape.Dims(2);
  const int num_output_pixels = output_height * output_width;

  // Filter words required to calculate each tranche
  const int filter_words_per_channel =
      filter_shape.Dims(1) * filter_shape.Dims(2) * filter_shape.Dims(3) / 4;
  const int filter_words_per_four_channels = filter_words_per_channel * 4;

  const int max_channels_per_tranche = FILTER_WORDS_PER_STORE *
                                       NUM_FILTER_STORES /
                                       filter_words_per_four_channels * 4;

  // Base address is byte address within 256K arena
  uint32_t input_base_addr = reinterpret_cast<uint32_t>(input_data) & 0x3ffff;

  // Configure static values
  cfu_set(REG_MODE, MODE_1);
  cfu_set(REG_INPUT_OFFSET, params.input_offset);
  cfu_set(REG_OUTPUT_OFFSET, params.output_offset);
  cfu_set(REG_OUTPUT_ACTIVATION_MIN, params.quantized_activation_min);
  cfu_set(REG_OUTPUT_ACTIVATION_MAX, params.quantized_activation_max);
  cfu_set(REG_INPUT_BASE_ADDR, input_base_addr);
  cfu_set(REG_NUM_PIXELS_X, output_width);
  cfu_set(REG_PIXEL_ADVANCE_X, input_depth / 16);
  cfu_set(REG_PIXEL_ADVANCE_Y, (input_depth / 16) * input_width);
  cfu_set(REG_INPUT_CHANNEL_DEPTH, input_depth);

  for (int channel = 0; channel < output_depth;
       channel += max_channels_per_tranche) {
    const int tranche_channels =
        std::min(max_channels_per_tranche, output_depth - channel);
    const int tranche_filter_words =
        filter_words_per_channel * tranche_channels;

    // Round up number of output values to multiple of 4 pixels
    const int tranche_output_values =
        (num_output_pixels + 3) / 4 * 4 * tranche_channels;

    // Configure
    cfu_set(REG_NUM_FILTER_WORDS, tranche_filter_words / 2);
    cfu_set(REG_NUM_OUTPUT_VALUES, tranche_output_values);
    cfu_set(REG_OUTPUT_CHANNEL_DEPTH, tranche_channels);

    // Reset to ensure important state is initialized
    cfu_set(REG_ACCELERATOR_RESET, 0);

    LoadPostProcessParameters(channel, tranche_channels, bias_data,
                              output_shift, output_multiplier);
    LoadFilterData(channel, tranche_channels, filter_shape,
                   reinterpret_cast<const uint32_t*>(filter_data));

    // Start Accelerator
    cfu_set(REG_ACCELERATOR_START, 0);

    // Collect data
    CollectOutput(channel, tranche_channels,
                  reinterpret_cast<uint32_t*>(output_data), num_output_pixels,
                  output_depth);
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
#endif  // GATEWARE_GEN
