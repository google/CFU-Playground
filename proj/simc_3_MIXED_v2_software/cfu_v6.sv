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

reg signed [INT32_SIZE-1:0] input_offset = 32'd0;
reg signed [INT32_SIZE-1:0] input_output_width = 32'd0;
reg signed [INT32_SIZE-1:0] input_depth = 32'd0;

reg signed [INT32_SIZE-1:0] acc = 0;
reg signed [INT32_SIZE-1:0] in_x_origin = 0;

always @(posedge clk) begin
    case (cmd)
        // Initialize
        0: begin    // Reset module
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
        10: begin    // Write input buffer
            input_buffer[address] <= value[7:0];
        end
        11: begin    // Write kernel weights buffer
            kernel_weights_buffer[address] <= value[7:0];
        end

        // Read buffers
        13: begin
            ret[7 : 0] <= input_buffer[address];
        end
        14: begin
            ret[7 : 0] <= kernel_weights_buffer[address];
        end

        // Write parameters
        20: begin
            input_offset <= value;
        end

        25: begin
            input_output_width <= value;
        end
        26: begin
            input_depth <= value;
        end

        41: begin 
            acc = 0;
            for (reg signed [INT32_SIZE-1:0] filter_x = 0; filter_x < 8; filter_x = filter_x + 1) begin
                reg signed [INT32_SIZE-1:0] in_x = in_x_origin + filter_x;
                for (reg signed [INT32_SIZE-1:0] in_channel = 0; in_channel < MAX_INPUT_CHANNELS; in_channel = in_channel + 1) begin
                    if ((in_x >= 0) && (in_x < input_output_width) && (in_channel < input_depth)) begin
                        acc += kernel_weights_buffer[filter_x * input_depth + in_channel] 
                            * (input_buffer[in_x * input_depth + in_channel] + input_offset);
                    end
                end
            end
        end
        42: begin
            in_x_origin <= value;
        end
        43: begin
            ret <= acc;
        end
    endcase
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
//   output wire [31:0]  rsp_payload_outputs_0,
//   input               reset,
//   input               clk
// );
//   wire output_buffer_valid;
  
//   wire [6:0] funct7;
//   assign funct7 = cmd_payload_function_id[9:3];
//   wire [31:0] ret;

//   conv1d CONV_1D(
//     .clk(clk),
//     .cmd(funct7),
//     .inp0(cmd_payload_inputs_0),
//     .inp1(cmd_payload_inputs_1),
//     .ret(rsp_payload_outputs_0),
//     .output_buffer_valid(output_buffer_valid)
//   );

//   // Only not ready for a command when we have a response.
//   assign cmd_ready = ~rsp_valid;

//   always @(posedge clk) begin
//     if (reset) begin
//       rsp_valid <= 1'b0;
//     end else if (rsp_valid) begin
//       // Waiting to hand off response to CPU.
//       rsp_valid <= ~rsp_ready;
//     end else if (cmd_valid) begin
//         rsp_valid <= output_buffer_valid;
//     end
//   end
// endmodule





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