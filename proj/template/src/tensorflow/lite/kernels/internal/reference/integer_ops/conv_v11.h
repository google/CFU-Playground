#include "conf.h"
#if CFU_VERSION == 11

#include "cfu_utils.h"
#include "common.h"
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/portable_tensor_utils.h"

namespace tflite {
namespace reference_integer_ops {
inline void ConvPerChannel(const ConvParams& params,
                           const int32_t* output_multiplier,
                           const int32_t* output_shift,
                           const RuntimeShape& input_shape,
                           const int8_t* input_data,
                           const RuntimeShape& filter_shape,
                           const int8_t* filter_data,
                           const RuntimeShape& bias_shape,
                           const int32_t* bias_data,
                           const RuntimeShape& output_shape,
                           int8_t* output_data) {
  // Initialize cfu
  cfu_op0(CFU_INITIALIZE, 0, 0);

  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  cfu_op0(CFU_WRITE_INPUT_OFFSET, 0, input_offset);

  const int pad_width = 3;
  (void)pad_width;

  const int32_t output_offset         = -128;
  const int32_t output_activation_min = -128;
  const int32_t output_activation_max = 127;

  cfu_op0(CFU_WRITE_OUTPUT_OFFSET, 0, output_offset);
  cfu_op0(CFU_WRITE_OUTPUT_ACTIVATION_MIN, 0, output_activation_min);
  cfu_op0(CFU_WRITE_OUTPUT_ACTIVATION_MAX, 0, output_activation_max);

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);

  const int input_width = input_shape.Dims(2);
  cfu_op0(CFU_WRITE_INPUT_OUTPUT_WIDTH, 0, input_width);

  const int filter_width = 8;
  (void)filter_width;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(CFU_WRITE_INPUT_DEPTH, 0, input_depth);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Quant parameters
    cfu_op0(CFU_WRITE_BIAS, 0, bias_data[out_channel]);
    cfu_op0(CFU_WRITE_OUTPUT_MULTIPLIER, 0, output_multiplier[out_channel]);
    cfu_op0(CFU_WRITE_OUTPUT_SHIFT, 0, output_shift[out_channel]);

    // Copy kernel
    for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(CFU_WRITE_FILTER_BUFFER, kernel_x * input_depth + in_channel, filter_data[addr]);
      }
    }

    int input_cur_x = -pad_width;
    // Copy input - first 8 xs
    for (int filter_x = 0; filter_x < 8; ++filter_x) {
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);

        // This is required to avoid mod in cfu
        if (input_depth == 2) {
          cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr + 8 * input_depth, value);
        }
      }
      ++input_cur_x;
    }

    int start_filter_x = 0;

    for (int out_x = 0; out_x < output_width; ++out_x) {
      cfu_op0(CFU_WRITE_START_FILTER_X, 0, start_filter_x);
      cfu_op0(CFU_START_COMPUTATION, 0, 0);
      while (!cfu_op0(CFU_FINISHED, 0, 0)) {
      };
      int32_t acc = cfu_op0(CFU_READ_ACCUMULATOR, 0, 0);

      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);

      // Copy input
      if (out_x == (output_width - 1)) {
        continue;
      }
      for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
        int buffer_addr = start_filter_x * input_depth + in_channel;
        int8_t value    = -input_offset;
        if ((input_cur_x >= 0) && (input_cur_x < input_width)) {
          int input_addr = input_cur_x * input_depth + in_channel;
          value          = input_data[input_addr];
        }
        cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr, value);

        // This is required to avoid mod in cfu
        if (input_depth == 2) {
          cfu_op0(CFU_WRITE_INPUT_BUFFER, buffer_addr + 8 * input_depth, value);
        }
      }
      ++input_cur_x;
      start_filter_x = (start_filter_x + 1) % 8;
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
#endif