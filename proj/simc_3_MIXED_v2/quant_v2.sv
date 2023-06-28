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
    // input  signed [INT32_SIZE-1:0] a,
    // input  signed [INT32_SIZE-1:0] b,
    input overflow,
    input signed [INT64_SIZE-1:0] ab_64,
    output signed [INT32_SIZE-1:0] ret
);

  // wire overflow = ((a == b) && (a == int32_t_min));
  // wire signed [INT64_SIZE-1:0] a_64 = a;
  // wire signed [INT64_SIZE-1:0] b_64 = b;
  // wire signed [INT64_SIZE-1:0] ab_64 = a_64 * b_64;
  wire signed [INT32_SIZE-1:0] nudge = (ab_64 > 0) ? one_shift_30 : (1 - one_shift_30);
  wire signed [INT32_SIZE-1:0] ab_x2_high32 = (ab_64 + nudge) / one_shift_31;

  assign ret = overflow ? int32_t_max : ab_x2_high32;

endmodule

module quant #(
    parameter INT32_SIZE  = 32,
    parameter INT64_SIZE  = 64,
    parameter int32_t_min = -2147483648
) (
    input clk,
    input signed [INT32_SIZE-1:0] acc,

    input start,
    output reg ret_valid = 0,

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
  // wire signed [INT32_SIZE-1:0] op1 = ((biased_acc) * (1 << left_shift));
  // wire signed [INT32_SIZE-1:0] op2 = output_multiplier;
  wire signed [INT64_SIZE-1:0] op1 = ((biased_acc) * (1 << left_shift));
  wire signed [INT64_SIZE-1:0] op2 = output_multiplier;

  wire overflow = ((op1 == op2) && (op1 == int32_t_min));

  wire signed [INT32_SIZE-1:0] SRDHM_ret;
  wire signed [INT32_SIZE-1:0] RDBP_ret;

  reg [7:0] state = 0;

  wire [31:0] a = op1[63:32];
  wire [31:0] b = op1[31:0];
  wire [31:0] c = op2[63:32];
  wire [31:0] d = op2[31:0];

  reg [63:0] ac_r;
  reg [63:0] bd_r;
  reg [63:0] bc_r;
  reg [63:0] ad_r;

  reg [63:0] ac_plus_bd_r;
  reg [63:0] bc_plus_ad_r;

  reg [63:0] ab64_r;


  // TODO: doesn't work correvtly for negative
  always @(posedge clk) begin
    if (start) begin
      state <= 1;
      bd_r  <= b * d;
      bc_r  <= b * c;
      ad_r  <= a * d;
      ac_r  <= a * c;
    end
    if (state == 1) begin
      // $display("quant state 1");
      state <= 2;
      ac_plus_bd_r <= bd_r + (ac_r << 64);
      bc_plus_ad_r <= (bc_r << 32) + (ad_r << 32);
    end
    if (state == 2) begin
      // $display("quant state 2");
      ab64_r <= ac_plus_bd_r + bc_plus_ad_r;
      state  <= 3;
    end
    if (state == 3) begin
      // $display("quant state 3, op1=%d, op2=%d, ab_64=%d", op1, op2, ab64_r);
      state <= 4;
      ret_valid <= 1;
    end
    if (state == 4) begin
      // $display("quant state 4");
      state <= 5;
    end
    if (state == 5) begin
      if (ret_valid) begin
        // $display("ret valid, state=%d", state);
        ret_valid <= 0;
      end
      state <= 0;
    end

  end

  saturating_rounding_doubling_high_mul SRDHM (
      // .a  (op1),
      // .b  (op2),
      .overflow(overflow),
      .ab_64(ab64_r),
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
