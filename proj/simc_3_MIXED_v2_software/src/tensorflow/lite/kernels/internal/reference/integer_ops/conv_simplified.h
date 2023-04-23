#include "conf.h"
#if CFU_VERSION == NO_CFU_SIMPLIFIED

#include "common.h"
#include "tensorflow/lite/kernels/internal/common.h"
#include "tensorflow/lite/kernels/internal/portable_tensor_utils.h"

namespace tflite {
namespace reference_integer_ops {

// Fixed-point per-channel-quantization convolution reference kernel.
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
  // Get parameters.
  const int32_t input_offset = params.input_offset;  // r = s(q - Z)

  const int pad_width = 3;

  const int32_t output_offset         = -128;
  const int32_t output_activation_min = -128;
  const int32_t output_activation_max = 127;

  const int output_depth = MatchingDim(filter_shape, 0, output_shape, 3);
  const int input_width  = input_shape.Dims(2);
  const int filter_width = 8;
  const int input_depth  = filter_shape.Dims(3);
  // const int output_width = output_shape.Dims(2);
  const int output_width = input_width;

  // input_shape = 1 x 1 x input_width x input_channels
  // kerne_shape = output_channels x 1 x 8 x input_channels
  // output_shaoe = 1 x 1 x output_width x output_channels

  // Original convolution code
  for (int out_x = 0; out_x < output_width; ++out_x) {
    const int in_x_origin = out_x - pad_width;
    for (int out_channel = 0; out_channel < output_depth; ++out_channel) {
      int32_t acc = 0;
      for (int filter_x = 0; filter_x < filter_width; ++filter_x) {
        const int in_x = in_x_origin + filter_x;

        // Zero padding by omitting the areas outside the image.
        const bool is_point_inside_image = (in_x >= 0) && (in_x < input_width);
        if (!is_point_inside_image) {
          continue;
        }

        // DEFAULT IMPLEMENTATION
        for (int in_channel = 0; in_channel < input_depth; ++in_channel) {
          int32_t input_val = input_data[in_x * input_depth + in_channel];
          int32_t filter_val =
              filter_data[out_channel * (8 * input_depth) + filter_x * input_depth + in_channel];

          acc += filter_val * (input_val + input_offset);
        }
      }
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