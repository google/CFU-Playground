module rounding_divide_by_POT #(
    parameter INT32_SIZE = 32
) (
    input  signed [INT32_SIZE-1:0] x,
    input  signed [INT32_SIZE-1:0] exponent,
    output signed [INT32_SIZE-1:0] ret
);

  wire signed [INT32_SIZE-1:0] mask = (1 << exponent) - 1;
  wire signed [INT32_SIZE-1:0] zero = 0;
  wire signed [INT32_SIZE-1:0] one = 1;
  wire signed [INT32_SIZE-1:0] remainder = x & mask;
  wire signed [INT32_SIZE-1:0] threshold = (mask >> 1) + (((x < zero) ? ~0 : 0) & one);

  assign ret = (x >>> exponent) + (((remainder > threshold) ? ~0 : 0) & one);

endmodule

module saturating_rounding_doubling_high_mul #(
    parameter INT32_SIZE   = 32,
    parameter INT64_SIZE   = 64,
    parameter one_shift_30 = (1 << 30),
    parameter one_shift_31 = (1 << 31),
    parameter int32_t_max  = 2147483647,
    parameter int32_t_min  = -2147483648
) (
    input  signed [INT32_SIZE-1:0] a,
    input  signed [INT32_SIZE-1:0] b,
    output signed [INT32_SIZE-1:0] ret
);

  wire overflow = ((a == b) && (a == int32_t_min));
  wire signed [INT64_SIZE-1:0] a_64 = a;
  wire signed [INT64_SIZE-1:0] b_64 = b;
  wire signed [INT64_SIZE-1:0] ab_64 = a_64 * b_64;
  wire signed [INT32_SIZE-1:0] nudge = (ab_64 > 0) ? one_shift_30 : (1 - one_shift_30);
  wire signed [INT32_SIZE-1:0] ab_x2_high32 = (ab_64 + nudge) / one_shift_31;

  assign ret = overflow ? int32_t_max : ab_x2_high32;

endmodule

module quant #(
  parameter INT32_SIZE = 32
)(
    input signed [INT32_SIZE-1:0] acc,

    input signed [INT32_SIZE-1:0] bias,
    input signed [INT32_SIZE-1:0] output_multiplier,
    input signed [INT32_SIZE-1:0] output_shift,
    input signed [INT32_SIZE-1:0] output_activation_min,
    input signed [INT32_SIZE-1:0] output_activation_max,
    input signed [INT32_SIZE-1:0] output_offset,

    output signed [INT32_SIZE-1:0] ret
);

  wire signed [INT32_SIZE-1:0] left_shift = (output_shift > 0) ? output_shift : 0;
  wire signed [INT32_SIZE-1:0] right_shift = (output_shift > 0) ? 0 : -output_shift;

  wire signed [INT32_SIZE-1:0] biased_acc = acc + bias;
  wire signed [INT32_SIZE-1:0] a = ((biased_acc) * (1 << left_shift));

  wire signed [INT32_SIZE-1:0] SRDHM_ret;
  wire signed [INT32_SIZE-1:0] RDBP_ret;

  saturating_rounding_doubling_high_mul SRDHM (
      .a  (a),
      .b  (output_multiplier),
      .ret(SRDHM_ret)
  );

  rounding_divide_by_POT RDBP (
      .x(-SRDHM_ret),
      .exponent(right_shift),
      .ret(RDBP_ret)
  );

  wire signed [INT32_SIZE-1:0] RDBP_ret_offseted = RDBP_ret + output_offset;

  wire signed [INT32_SIZE-1:0] bound_lower_ret = RDBP_ret_offseted < output_activation_min ? output_activation_min : RDBP_ret_offseted;
  wire signed [INT32_SIZE-1:0] bound_lower_higher_ret = bound_lower_ret > output_activation_max ? output_activation_max : bound_lower_ret;

  assign ret = bound_lower_higher_ret;

endmodule