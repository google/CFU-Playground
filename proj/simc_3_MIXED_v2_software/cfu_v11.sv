// Difference from v9 - calculates quantization

// module conv1d #(
//     parameter BYTE_SIZE  = 8,
//     parameter INT32_SIZE = 32
// ) (
//     input                       clk,
//     input      [           6:0] cmd,
//     input      [INT32_SIZE-1:0] inp0,
//     input      [INT32_SIZE-1:0] inp1,
//     output reg [INT32_SIZE-1:0] ret,
//     output reg                  output_buffer_valid = 1
// );
//   localparam PADDING = 4;  // (8 / 2)
//   localparam MAX_INPUT_SIZE = 1024;
//   localparam MAX_INPUT_CHANNELS = 128;
//   localparam KERNEL_LENGTH = 8;

//   localparam SUM_AT_ONCE = 8;
//   localparam BUFFERS_SIZE = KERNEL_LENGTH * MAX_INPUT_CHANNELS;

//   wire [INT32_SIZE-1:0] address = inp0;
//   wire [INT32_SIZE-1:0] value = inp1;
//   wire [INT32_SIZE-1:0] cur_buffer_size = KERNEL_LENGTH * input_depth;

//   // Buffers
//   (* RAM_STYLE="BLOCK" *)
//   reg signed [BYTE_SIZE-1:0] input_buffer[0:BUFFERS_SIZE - 1];

//   (* RAM_STYLE="BLOCK" *)
//   reg signed [BYTE_SIZE-1:0] kernel_weights_buffer[0:BUFFERS_SIZE - 1];

//   // Parameters
//   reg signed [INT32_SIZE-1:0] input_offset = 32'd0;
//   // reg signed [INT32_SIZE-1:0] input_output_width = 32'd0;
//   reg signed [INT32_SIZE-1:0] input_depth = 32'd0;

//   // Computation related registers
//   reg signed [INT32_SIZE-1:0] start_filter_x = 0;
//   reg finished_work = 1'b1;
//   reg update_address = 1'b0;
//   reg [INT32_SIZE-1:0] kernel_addr;
//   reg [INT32_SIZE-1:0] input_addr;
//   reg signed [INT32_SIZE-1:0] acc;

//   always @(posedge clk) begin
//     if (!finished_work) begin
//       if (update_address) begin
//         kernel_addr <= kernel_addr + SUM_AT_ONCE;
//         if ((input_addr + SUM_AT_ONCE) >= cur_buffer_size) begin
//           input_addr <= input_addr + SUM_AT_ONCE - cur_buffer_size;
//         end else begin
//           input_addr <= input_addr + SUM_AT_ONCE;
//         end
//         update_address <= 0;
//       end else begin
//         if (kernel_addr >= cur_buffer_size) begin
//           finished_work <= 1;
//         end else begin
//           acc <= acc + 
//             kernel_weights_buffer[kernel_addr     ] * (input_buffer[(input_addr    )] + input_offset) + 
//             kernel_weights_buffer[kernel_addr +  1] * (input_buffer[(input_addr + 1)] + input_offset) + 
//             kernel_weights_buffer[kernel_addr +  2] * (input_buffer[(input_addr + 2)] + input_offset) + 
//             kernel_weights_buffer[kernel_addr +  3] * (input_buffer[(input_addr + 3)] + input_offset) +
//             kernel_weights_buffer[kernel_addr +  4] * (input_buffer[(input_addr + 4)] + input_offset) + 
//             kernel_weights_buffer[kernel_addr +  5] * (input_buffer[(input_addr + 5)] + input_offset) + 
//             kernel_weights_buffer[kernel_addr +  6] * (input_buffer[(input_addr + 6)] + input_offset) + 
//             kernel_weights_buffer[kernel_addr +  7] * (input_buffer[(input_addr + 7)] + input_offset);
//         end
//         update_address <= 1;
//       end

//     end

//     case (cmd)
//       // Initialize
//       0: begin  // Reset module
//         // Fill input with zeros
//         ret <= BUFFERS_SIZE;
//       end

//       // Write buffers
//       1: begin  // Write input buffer
//         // if (address < BUFFERS_SIZE) begin
//         input_buffer[address] <= value[7:0];
//         // end
//       end
//       2: begin  // Write kernel weights buffer
//         // if (address < BUFFERS_SIZE) begin
//         kernel_weights_buffer[address] <= value[7:0];
//         // end
//       end

//       // Write parameters
//       3: begin
//         input_offset <= value;
//       end

//       4: begin
//         // input_output_width <= value;
//         ret <= 0;
//       end
//       5: begin
//         input_depth <= value;
//       end

//       6: begin  // Start computation
//         acc <= 0;
//         finished_work <= 0;
//         update_address <= 0;
//         kernel_addr <= 0;
//         input_addr  <= start_filter_x * input_depth;
//       end

//       7: begin  // get acumulator
//         ret <= acc;
//       end
//       8: begin  // Write start x in input ring buffer 
//         start_filter_x <= value;
//       end
//       9: begin  // Check if computation is done
//         ret <= finished_work;
//       end
//       // 10: begin
//       //   ret <= input_buffer[address];
//       // end
//       // 11: begin
//       //   ret <= kernel_weights_buffer[address];
//       // end
//       default: begin
//         // $display("!!! DEFAULT case ");
//         ret <= 0;
//       end
//     endcase
//   end

// endmodule

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

  assign ret = (x >> exponent) + (((remainder > threshold) ? ~0 : 0) & one);

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
    parameter BYTE_SIZE  = 8,
    parameter INT32_SIZE = 32
) (
    input                       clk,
    input      [           6:0] cmd,
    input      [INT32_SIZE-1:0] inp0,
    input      [INT32_SIZE-1:0] inp1,
    output reg [INT32_SIZE-1:0] ret,
    output reg                  output_buffer_valid = 1
);

  reg signed [INT32_SIZE-1:0] bias;
  reg signed [INT32_SIZE-1:0] output_multiplier;
  reg signed [INT32_SIZE-1:0] output_shift;
  reg signed [INT32_SIZE-1:0] output_activation_min;
  reg signed [INT32_SIZE-1:0] output_activation_max;
  reg signed [INT32_SIZE-1:0] output_offset;

  wire signed [INT32_SIZE-1:0] left_shift = (output_shift > 0) ? output_shift : 0;
  wire signed [INT32_SIZE-1:0] right_shift = (output_shift > 0) ? 0 : -output_shift;

  wire signed [INT32_SIZE-1:0] a = (inp1 * (1 << left_shift));

  wire signed [INT32_SIZE-1:0] SRDHM_ret;
  wire signed [INT32_SIZE-1:0] RDBP_ret;

  saturating_rounding_doubling_high_mul SRDHM (
      .a  (a),
      .b  (output_multiplier),
      .ret(SRDHM_ret)
  );

  rounding_divide_by_POT RDBP (
      .x(SRDHM_ret),
      .exponent(right_shift),
      .ret(RDBP_ret)
  );

  always @(posedge clk) begin
    case (cmd)
      // Initialize
      0: begin  // Reset module
        ret <= 0;
      end

      1: begin
        bias <= inp1;
      end

      2: begin
        output_multiplier <= inp1;
      end

      3: begin
        output_shift <= inp1;
      end

      4: begin
        output_activation_min <= inp1;
      end

      5: begin
        output_activation_max <= inp1;
      end

      6: begin
        output_offset <= inp1;
      end

      7: begin
        ret <= -RDBP_ret;
      end

      default: begin
        // $display("!!! DEFAULT case ");
        ret <= 0;
      end
    endcase
  end

endmodule

