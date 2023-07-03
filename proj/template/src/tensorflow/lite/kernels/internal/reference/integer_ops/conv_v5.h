#include "conf.h"
#if CFU_VERSION == 5

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
  // static int call = 0;
  // Initialize cfu
  cfu_op0(0, 0, 0);

  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)
  cfu_op0(20, 0, input_offset);

  const int pad_width = 3;
  (void)pad_width;

  const int32_t output_offset = -128;
  cfu_op0(21, 0, output_offset);
  const int32_t output_activation_min = -128;
  cfu_op0(22, 0, output_activation_min);
  const int32_t output_activation_max = 127;
  cfu_op0(23, 0, output_activation_max);

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  cfu_op0(24, 0, output_depth);

  const int input_width = input_shape.Dims(2);
  cfu_op0(25, 0, input_width);

  const int filter_width = 8;
  (void)filter_width;

  const int input_depth = filter_shape.Dims(3);
  cfu_op0(26, 0, input_depth);

  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  // Copy input
  for (int in_x = 0; in_x < input_width; ++in_x) {
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      int addr = in_x * input_depth + in_channel;
      cfu_op0(10, addr, input_data[addr]);
    }
  }
  // printf("Done copying input\n");

  for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
    // Copy kernel
    for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
      for (int kernel_x = 0; kernel_x < filter_width; ++kernel_x) {
        int addr = out_channel * (8 * input_depth) + kernel_x * input_depth + in_channel;
        cfu_op0(11, kernel_x * input_depth + in_channel, filter_data[addr]);
      }
    }
    cfu_op0(27, 0, bias_data[out_channel]);

    for (int out_x = 0; out_x < output_width; ++out_x) {
      const int in_x_origin = out_x - pad_width;

      cfu_op0(42, 0, in_x_origin);
      cfu_op0(41, 0, 0);
      int32_t acc = cfu_op0(43, 0, 0);

      if (bias_data) {
        acc += bias_data[out_channel];
      }
      acc = multiply_by_quant_mult(acc, output_multiplier[out_channel], output_shift[out_channel]);

      acc += output_offset;
      acc               = std::max(acc, output_activation_min);
      acc               = std::min(acc, output_activation_max);
      int addr          = out_x * output_depth + out_channel;
      output_data[addr] = static_cast<int8_t>(acc);
    }
  }
}

}  // namespace reference_integer_ops
}  // namespace tflite
#endif