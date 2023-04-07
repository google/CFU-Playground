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
localparam MAX_PADDED_INPUT_SIZE = 1024 + 2 * PADDING;
localparam MAX_INPUT_CHANNELS = 128;
localparam CONVOLUTE_AT_ONCE = 8;

// Kerbel has size (1, 8)
localparam KERNEL_LENGTH = 8;


wire [INT32_SIZE-1:0] address = inp0;

wire [INT32_SIZE-1:0] input_row = address / MAX_INPUT_CHANNELS;
wire [INT32_SIZE-1:0] input_col = address % MAX_INPUT_CHANNELS;

wire [INT32_SIZE-1:0] kernel_row = address / MAX_INPUT_CHANNELS;
wire [INT32_SIZE-1:0] kernel_col = address % MAX_INPUT_CHANNELS;

// INPUT/OUTPUT BUFFER
reg [INT32_SIZE-1:0]       buffer_size;
// Input buffer has shape of (1024 + 8) x 128 
reg signed [BYTE_SIZE*2:0] input_buffer          [0:MAX_INPUT_SIZE + 2 * PADDING - 1] [0:MAX_INPUT_CHANNELS-1];
// kernel weights buffer has shape of 8 x 128 
reg signed [BYTE_SIZE*2:0] kernel_weights_buffer [0:KERNEL_LENGTH - 1] [0: MAX_INPUT_CHANNELS-1];
// output buffer has a shape of 1024
reg signed [INT32_SIZE:0] output_buffer         [0:MAX_INPUT_SIZE - 1];

// Convolution
reg signed [BYTE_SIZE-1:0] bias = 8'd0;
reg signed [BYTE_SIZE:0] input_offset = 8'd0;
// reg signed [BYTE_SIZE-1:0] working_regs [0:CONVOLUTE_AT_ONCE-1] [0:KERNEL_LENGTH-1];

always @(posedge clk) begin
    case (cmd)
        0: begin    // Reset module
            // Fill output with zeros
            for (reg [INT32_SIZE-1:0] out_idx = 0; out_idx < MAX_INPUT_SIZE; out_idx = out_idx + 1) begin
                output_buffer[out_idx] = 0;
            end 

            // Fill input with zeros
            for (reg [INT32_SIZE-1:0] in_idx = 0; in_idx < MAX_PADDED_INPUT_SIZE; in_idx = in_idx + 1) begin
                for (reg [INT32_SIZE-1:0] channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; channel_idx = channel_idx + 1) begin
                    input_buffer[in_idx][channel_idx] = 0;
                end   
            end 

            // Fill kernel_weights_buffer with zeros
            for (reg [INT32_SIZE-1:0] channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; channel_idx = channel_idx + 1) begin
                for (reg [INT32_SIZE-1:0] kernel_idx = 0; kernel_idx < KERNEL_LENGTH; kernel_idx = kernel_idx + 1) begin
                    kernel_weights_buffer[kernel_idx][channel_idx] = 0;
                end   
            end 
        end 
        1: begin    // Write input buffer
            // Note that processor is little-endian
            input_buffer[input_row][input_col    ] <= inp1[7 : 0];
            input_buffer[input_row][input_col + 1] <= inp1[15: 8];
            input_buffer[input_row][input_col + 2] <= inp1[23:16];
            input_buffer[input_row][input_col + 3] <= inp1[31:24];
        end
        2: begin    // Write kernel weights buffer
            // $display("kernel row: %d", kernel_row);
            kernel_weights_buffer[kernel_row][kernel_col    ] <= inp1[7 : 0];
            kernel_weights_buffer[kernel_row][kernel_col + 1] <= inp1[15: 8];
            kernel_weights_buffer[kernel_row][kernel_col + 2] <= inp1[23:16];
            kernel_weights_buffer[kernel_row][kernel_col + 3] <= inp1[31:24];
        end
        3: begin    // Read output buffer
            ret[7 : 0] <= output_buffer[address][31:24] >> 1;
            ret[15: 8] <= output_buffer[address][23:16] >> 1;
            ret[23:16] <= output_buffer[address][15: 8] >> 1;
            ret[31:24] <= output_buffer[address][7 : 0] >> 1;

            // ret[7 : 0] <= output_buffer[address    ] >> 1;
            // ret[15: 8] <= output_buffer[address + 1] >> 1;
            // ret[23:16] <= output_buffer[address + 2] >> 1;
            // ret[31:24] <= output_buffer[address + 3] >> 1;
        end
        4: begin    // Start computation
            // output_buffer_valid = 0;
            for (reg [INT32_SIZE-1:0] out_idx = 0; out_idx < MAX_INPUT_SIZE; out_idx = out_idx + 1) begin
                for (reg [INT32_SIZE-1:0] channel_idx = 0; channel_idx < MAX_INPUT_CHANNELS; channel_idx = channel_idx + 1) begin
                    output_buffer[out_idx] += 
                        input_buffer[(PADDING + out_idx - 3)][channel_idx] * (kernel_weights_buffer[0][channel_idx] + input_offset) + 
                        input_buffer[(PADDING + out_idx - 2)][channel_idx] * (kernel_weights_buffer[1][channel_idx] + input_offset) + 
                        input_buffer[(PADDING + out_idx - 1)][channel_idx] * (kernel_weights_buffer[2][channel_idx] + input_offset) + 
                        input_buffer[(PADDING + out_idx    )][channel_idx] * (kernel_weights_buffer[3][channel_idx] + input_offset) + 
                        input_buffer[(PADDING + out_idx + 1)][channel_idx] * (kernel_weights_buffer[4][channel_idx] + input_offset) + 
                        input_buffer[(PADDING + out_idx + 2)][channel_idx] * (kernel_weights_buffer[5][channel_idx] + input_offset) + 
                        input_buffer[(PADDING + out_idx + 3)][channel_idx] * (kernel_weights_buffer[6][channel_idx] + input_offset) + 
                        input_buffer[(PADDING + out_idx + 4)][channel_idx] * (kernel_weights_buffer[7][channel_idx] + input_offset);
                end
                output_buffer[out_idx] += bias; 
            end
            // output_buffer_valid = 1;
        end
        5: begin    // Read input buffer
            ret[7 : 0] <= input_buffer[input_row][input_col    ];
            ret[15: 8] <= input_buffer[input_row][input_col + 1];
            ret[23:16] <= input_buffer[input_row][input_col + 2];
            ret[31:24] <= input_buffer[input_row][input_col + 3];
        end
        6: begin    // Read kernel_weights buffer
            ret[7 : 0] <= kernel_weights_buffer[kernel_row][kernel_col    ];
            ret[15: 8] <= kernel_weights_buffer[kernel_row][kernel_col + 1];
            ret[23:16] <= kernel_weights_buffer[kernel_row][kernel_col + 2];
            ret[31:24] <= kernel_weights_buffer[kernel_row][kernel_col + 3];
        end
        7: begin    // Write bias
            bias <= inp0;
        end
        8: begin    // Write input offset
            input_offset <= inp0;
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


// Testbench Code Goes here
// module conv1d_tb;
// reg clk;
// reg [6:0]  cmd;
// reg signed [31:0] inp0, inp1;
// wire output_buffer_valid;
// wire signed [31:0] ret;

// initial begin
//     $monitor ("cmd=%d | inp0=%h | inp1=%h | output_valid=%d | ret=%h", cmd, inp0, inp1, output_buffer_valid, ret);
//     clk = 0;
//     cmd = 0;
//     inp0 = 0;
//     inp1 = 0;

//     $display("Write data to input buffer");
//     #15 cmd = 1; inp0 = 0; inp1 = {8'd7, 8'd6, 8'd5, 8'd4};   // write input_buffer[0:3] = 7;
//     #10 cmd = 1; inp0 = 1; inp1 = {8'd3, 8'd2, 8'd1, 8'd0};   // write input_buffer[4:7] = 6;

//     #10 $display("Read data from input buffer");
//         cmd = 6; inp0 = 0;              // read  input_buffer[0:3]
//     #10 cmd = 6; inp0 = 1;              // read  input_buffer[4:7]
//     #10 cmd = 6; inp0 = 2;              // read  input_buffer[4:7]

//     #10 $display("Write data to kernel weights buffer");
//         cmd = 2; inp0 = 0; inp1 = {8'd2, 8'd2, 8'd2, 8'd2};   // write kernel_weights_buffer[0:3] = 7;
//     #10 cmd = 2; inp0 = 1; inp1 = {8'd2, 8'd2, 8'd2, 8'd2};   // write kernel_weights_buffer[4:7] = 6;

//     #10 $display("Read data from kernel weights buffer");
//         cmd = 7; inp0 = 0;              // read  kernel weights buffer[0:3]
//     #10 cmd = 7; inp0 = 1;              // read  kernel weights buffer[4:7]

//     #10 $display("Set bias");
//         cmd = 8; inp0 = 1;

//     #10 $display("Set buffer size");
//         cmd = 4; inp0 = 8; inp1 = 0;
    
//     #10 $display("Start calculations.");
//         cmd = 5;

//     #30 $display("Read output");
//         cmd = 3; inp0 = 0; inp1 = 0;
//     #20 cmd = 3; inp0 = 1;
//     #10 $finish;
// end

// always begin
//     #5 clk = !clk;
// end

// conv1d U0 (
//     .clk (clk),
//     .cmd (cmd),
//     .inp0 (inp0),
//     .inp1 (inp1),
//     .output_buffer_valid(output_buffer_valid),
//     .ret (ret)
// );

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
