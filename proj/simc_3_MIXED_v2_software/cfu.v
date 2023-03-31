/*
    cmd: 
        - 0 - initialize - Fills paddings with 0
        - 1 - write to input buffer
            - inp0 - address / 4
            - inp1 - 4 values
        - 2 - write to kernel weights buffer
            - inp0 - address / 4
            - inp1 - 4 values
        - 3 - read from output_buffer 
            - inp0 - address / 4
        - 4 - start computation
        
        // debug purposes
        - 5 - read from the input buffer
            - inp0 - address / 4
        - 6 - read from the kernel weights
            - inp0 - addres / 4

        // 
        - 7 - set bias
            - inp0 - bias
        - 8 - set input offset
            - inp0 - input_offset
        
*/
module conv1d #(
    parameter BYTE_SIZE = 8,
    parameter INT32_SIZE = 32
)(
    input                         clk,
    input       [6:0]             cmd,
    input       [INT32_SIZE-1:0]  inp0,
    input       [INT32_SIZE-1:0]  inp1,
    output reg  [INT32_SIZE-1:0]  ret,
    output reg                    output_buffer_valid = 1
);
localparam PADDING = 4; // (8 / 2)
localparam MAX_INPUT_SIZE = 1024;
localparam MAX_INPUT_CHANNELS = 128;
localparam KERNEL_LENGTH = 8;


wire [INT32_SIZE-1:0] address = inp0;
wire [INT32_SIZE-1:0] value   = inp1;

// INPUT/OUTPUT BUFFER
reg [INT32_SIZE-1:0]       buffer_size;
// Input buffer has shape of 1024 x 128 
reg signed [BYTE_SIZE-1:0] input_buffer          [0:MAX_INPUT_SIZE * MAX_INPUT_CHANNELS - 1];
// kernel weights buffer has shape of 8 x 128 
reg signed [BYTE_SIZE-1:0] kernel_weights_buffer [0:KERNEL_LENGTH * MAX_INPUT_CHANNELS - 1];
// output buffer has a shape of 1024
reg signed [INT32_SIZE:0]  output_buffer         [0:MAX_INPUT_SIZE - 1];

reg signed [INT32_SIZE-1:0] input_offset = 32'd0;
reg signed [INT32_SIZE-1:0] output_offset = 32'd0;
reg signed [INT32_SIZE-1:0] output_activation_min = 32'd0;
reg signed [INT32_SIZE-1:0] output_activation_max = 32'd0;
reg signed [INT32_SIZE-1:0] output_depth = 32'd0;
reg signed [INT32_SIZE-1:0] input_output_width = 32'd0;
reg signed [INT32_SIZE-1:0] input_depth = 32'd0;

reg signed [INT32_SIZE-1:0] bias = 32'd0;
reg signed [INT32_SIZE-1:0] output_multiplier = 32'd0;
reg signed [INT32_SIZE-1:0] output_shift = 32'd0;


always @(posedge clk) begin
    // Note that processor is little-endian
    case (cmd)
        // Initialize
        0: begin    // Reset module
            // Fill output with zeros
            for (reg [INT32_SIZE-1:0] out_x = 0; out_x < MAX_INPUT_SIZE; out_x = out_x + 1) begin
                output_buffer[out_x] = 0;
            end 

            // Fill input with zeros
            for (reg [INT32_SIZE-1:0] in_idx = 0; in_idx < MAX_INPUT_SIZE * MAX_INPUT_CHANNELS; in_idx = in_idx + 1) begin
                input_buffer[in_idx] = 0;
            end 

            // Fill kernel_weights_buffer with zeros
            for (reg [INT32_SIZE-1:0] kernel_idx = 0; kernel_idx < KERNEL_LENGTH * MAX_INPUT_CHANNELS; kernel_idx = kernel_idx + 1) begin
                kernel_weights_buffer[kernel_idx] = 0;
            end   
        end 

        // Write buffers
        1: begin    // Write input buffer
            input_buffer[address] <= value[7:0];
        end
        2: begin    // Write kernel weights buffer
            // Note that processor is little-endian
            kernel_weights_buffer[address] <= value[7:0];
        end

        // Read buffers
        3: begin    // Read output buffer
            // Note that processor is little-endian
            ret[7 : 0] <= output_buffer[address][31:24];
            ret[15: 8] <= output_buffer[address][23:16];
            ret[23:16] <= output_buffer[address][15: 8];
            ret[31:24] <= output_buffer[address][7 : 0];
        end
        4: begin
            ret[7 : 0] <= input_buffer[address];
            ret[15: 8] <= 0;
            ret[23:16] <= 0;
            ret[31:24] <= 0;
        end
        5: begin
            ret[7 : 0] <= kernel_weights_buffer[address];
            ret[15: 8] <= 0;
            ret[23:16] <= 0;
            ret[31:24] <= 0;
        end
        6: begin    // Zero out output buffer
            for (reg [INT32_SIZE-1:0] out_x = 0; out_x < MAX_INPUT_SIZE; out_x = out_x + 1) begin
                output_buffer[out_x] = 0;
            end 
        end

        // Write parameters
        7: begin
            input_offset[7 : 0] <= value[31:24];
            input_offset[15: 8] <= value[23:16];
            input_offset[23:16] <= value[15: 8];
            input_offset[31:24] <= value[7 : 0];
        end
        8: begin
            output_offset[7 : 0] <= value[31:24];
            output_offset[15: 8] <= value[23:16];
            output_offset[23:16] <= value[15: 8];
            output_offset[31:24] <= value[7 : 0];
        end
        9: begin
            output_activation_min[7 : 0] <= value[31:24];
            output_activation_min[15: 8] <= value[23:16];
            output_activation_min[23:16] <= value[15: 8];
            output_activation_min[31:24] <= value[7 : 0];
        end
        10: begin
            output_activation_max[7 : 0] <= value[31:24];
            output_activation_max[15: 8] <= value[23:16];
            output_activation_max[23:16] <= value[15: 8];
            output_activation_max[31:24] <= value[7 : 0];
        end
        11: begin
            output_depth[7 : 0] <= value[31:24];
            output_depth[15: 8] <= value[23:16];
            output_depth[23:16] <= value[15: 8];
            output_depth[31:24] <= value[7 : 0];
        end
        12: begin
            input_output_width[7 : 0] <= value[31:24];
            input_output_width[15: 8] <= value[23:16];
            input_output_width[23:16] <= value[15: 8];
            input_output_width[31:24] <= value[7 : 0];
        end
        13: begin
            input_depth[7 : 0] <= value[31:24];
            input_depth[15: 8] <= value[23:16];
            input_depth[23:16] <= value[15: 8];
            input_depth[31:24] <= value[7 : 0];
        end
        14: begin
            bias[7 : 0] <= value[31:24];
            bias[15: 8] <= value[23:16];
            bias[23:16] <= value[15: 8];
            bias[31:24] <= value[7 : 0];
        end
        15: begin
            output_multiplier[7 : 0] <= value[31:24];
            output_multiplier[15: 8] <= value[23:16];
            output_multiplier[23:16] <= value[15: 8];
            output_multiplier[31:24] <= value[7 : 0];
        end
        16: begin
            output_shift[7 : 0] <= value[31:24];
            output_shift[15: 8] <= value[23:16];
            output_shift[23:16] <= value[15: 8];
            output_shift[31:24] <= value[7 : 0];
        end

        17: begin    // Start computation
            // output_buffer_valid = 0;
            for (reg signed [INT32_SIZE-1:0] out_x = 0; out_x < MAX_INPUT_SIZE; out_x = out_x + 1) begin
                for (reg signed [INT32_SIZE-1:0] filter_x = 0; filter_x < 8; filter_x = filter_x + 1) begin
                    for (reg signed [INT32_SIZE-1:0] in_channel = 0; in_channel < MAX_INPUT_CHANNELS; in_channel = in_channel + 1) begin
                      if ( ((out_x - 3 + filter_x) >= 0) && ((out_x - 3 + filter_x) <= input_output_width) && (in_channel < input_depth)) begin
                          output_buffer[out_x] += 
                            input_buffer[(out_x - 3 + filter_x) * input_depth + in_channel] * (kernel_weights_buffer[0 * input_depth + in_channel] + input_offset);
                      end
                    end
                end
                output_buffer[out_x] += bias; 
            end
            // output_buffer_valid = 1;
        end
    endcase
end
    
endmodule

module Cfu (
  input               cmd_valid,
  output              cmd_ready,
  input      [9:0]    cmd_payload_function_id,
  input      [31:0]   cmd_payload_inputs_0,
  input      [31:0]   cmd_payload_inputs_1,
  output reg          rsp_valid,
  input               rsp_ready,
  output wire [31:0]  rsp_payload_outputs_0,
  input               reset,
  input               clk
);
  wire output_buffer_valid;
  
  wire [6:0] funct7;
  assign funct7 = cmd_payload_function_id[9:3];
  wire [31:0] ret;

  conv1d CONV_1D(
    .clk(clk),
    .cmd(funct7),
    .inp0(cmd_payload_inputs_0),
    .inp1(cmd_payload_inputs_1),
    .ret(rsp_payload_outputs_0),
    .output_buffer_valid(output_buffer_valid)
  );

  // Only not ready for a command when we have a response.
  assign cmd_ready = ~rsp_valid;

  always @(posedge clk) begin
    if (reset) begin
      rsp_valid <= 1'b0;
    end else if (rsp_valid) begin
      // Waiting to hand off response to CPU.
      rsp_valid <= ~rsp_ready;
    end else if (cmd_valid) begin
        rsp_valid <= output_buffer_valid;
    end
  end
endmodule





// module Cfu (
//   input               cmd_valid,
//   output              cmd_ready,
//   input      [9:0]    cmd_payload_function_id,
//   input      [31:0]   cmd_payload_inputs_0,
//   input      [31:0]   cmd_payload_inputs_1,
//   output reg          rsp_valid,
//   input               rsp_ready,
//   output reg [31:0]   rsp_payload_outputs_0,
//   input               reset,
//   input               clk
// );
//   // localparam InputOffset = $signed(9'd128);
//   reg signed [8:0] input_offset = 128;
  
//   wire [6:0] funct7;
//   assign funct7 = cmd_payload_function_id[9:3];

//   // SIMD multiply step:
//   wire signed [15:0] prod_0, prod_1, prod_2, prod_3;
//   assign prod_0 =  ($signed(cmd_payload_inputs_0[7 : 0]) + input_offset)
//                   * $signed(cmd_payload_inputs_1[7 : 0]);
//   assign prod_1 =  ($signed(cmd_payload_inputs_0[15: 8]) + input_offset)
//                   * $signed(cmd_payload_inputs_1[15: 8]);
//   assign prod_2 =  ($signed(cmd_payload_inputs_0[23:16]) + input_offset)
//                   * $signed(cmd_payload_inputs_1[23:16]);
//   assign prod_3 =  ($signed(cmd_payload_inputs_0[31:24]) + input_offset)
//                   * $signed(cmd_payload_inputs_1[31:24]);

//   wire signed [31:0] sum_prods;
//   assign sum_prods = prod_0 + prod_1 + prod_2 + prod_3;

//   // Only not ready for a command when we have a response.
//   assign cmd_ready = ~rsp_valid;

//   always @(posedge clk) begin
//     if (reset) begin
//       rsp_payload_outputs_0 <= 32'b0;
//       rsp_valid <= 1'b0;
//     end else if (rsp_valid) begin
//       // Waiting to hand off response to CPU.
//       rsp_valid <= ~rsp_ready;
//     end else if (cmd_valid) begin
//       rsp_valid <= 1'b1;
//       // Accumulate step:
//       if (funct7 == 0) begin
//         rsp_payload_outputs_0 <= rsp_payload_outputs_0 + sum_prods;
//       end else if (funct7 == 1) begin
//         rsp_payload_outputs_0 <= 32'b0;
//       end else if (funct7 == 2) begin
//         input_offset <= cmd_payload_inputs_0;
//       end else begin
//         rsp_payload_outputs_0 <= input_offset;
//       end
//       // rsp_payload_outputs_0 <= |cmd_payload_function_id[9:3]
//       //     ? 32'b0
//       //     : rsp_payload_outputs_0 + sum_prods;
//     end
//   end
// endmodule