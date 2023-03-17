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
        - 4 - read buffer_size
        - 5 - start computation
        
        // debug purposes
        - 6 - read from the input buffer
            - inp0 - address / 4
        - 7 - read from the kernel weights
            - inp0 - addres / 4

        // 
        - 8 - set bias
            - inp0 - bias
        
*/
module conv1d #(
    parameter BYTE_SIZE = 8,
    parameter INT32_SIZE = 32
)(
    input                         clk,
    input       [6:0]             cmd,
    input       [INT32_SIZE-1:0]   inp0,
    input       [INT32_SIZE-1:0]   inp1,
    output reg  [INT32_SIZE-1:0]   ret,
    output reg                    output_buffer_valid = 1
);
// Kernel has size (1, 8)
localparam KERNEL_LENGTH = 8;
localparam PADDING = 4; // (8 / 2)
localparam CONVOLUTE_AT_ONCE = 8;
localparam OUTPUT_BUFFER_SIZE = CONVOLUTE_AT_ONCE;


wire [INT32_SIZE-1:0] address = inp0 * 4;


// Warning: input buffer is on 8 bytes bigger then output, because of padding. 
// User should fill paddings themself correcly if they want to get correct value
reg signed [BYTE_SIZE-1:0] input_buffer          [0:OUTPUT_BUFFER_SIZE + 2 * PADDING - 1];
reg signed [BYTE_SIZE-1:0] kernel_weights_buffer [0:KERNEL_LENGTH - 1];
reg signed [BYTE_SIZE-1:0] output_buffer         [0:OUTPUT_BUFFER_SIZE - 1];

// Convolution
reg [INT32_SIZE-1:0] convolution_pointer = PADDING;     
reg increment_pointer_phase;
reg [BYTE_SIZE-1:0] bias = 8'b0;

always @(posedge clk) begin
    if (!output_buffer_valid) begin
        if (!increment_pointer_phase) begin
            for (reg [INT32_SIZE-1:0] idx = 0; idx < CONVOLUTE_AT_ONCE; idx = idx + 1) begin
                // Since size is even, the offset are the following:
                // -4 -3 -2 -1 0 +1 +2 +3
                // output_buffer[convolution_pointer + idx - PADDING] = 0;
                // for (reg [INT32_SIZE-1:0] jdx = 0; jdx < KERNEL_LENGTH; jdx = jdx + 1) begin
                //     // working_regs[idx][jdx] = input_buffer[(convolution_pointer + idx + jdx - PADDING)] * kernel_weights_buffer[jdx];
                //     output_buffer[convolution_pointer + idx - PADDING] = output_buffer[convolution_pointer + idx - PADDING] + input_buffer[(convolution_pointer + idx + jdx - 4)] * kernel_weights_buffer[jdx];
                // end
                // output_buffer[convolution_pointer + idx - PADDING] = working_regs[idx][0] + working_regs[idx][1] + working_regs[idx][2] + working_regs[idx][3] + working_regs[idx][4] + working_regs[idx][5] + working_regs[idx][6] + working_regs[idx][7];

                output_buffer[convolution_pointer + idx - PADDING] <= input_buffer[(convolution_pointer + idx - 4)] * kernel_weights_buffer[0] + 
                                                                      input_buffer[(convolution_pointer + idx - 3)] * kernel_weights_buffer[1] + 
                                                                      input_buffer[(convolution_pointer + idx - 2)] * kernel_weights_buffer[2] + 
                                                                      input_buffer[(convolution_pointer + idx - 1)] * kernel_weights_buffer[3] + 
                                                                      input_buffer[(convolution_pointer + idx    )] * kernel_weights_buffer[4] + 
                                                                      input_buffer[(convolution_pointer + idx + 1)] * kernel_weights_buffer[5] + 
                                                                      input_buffer[(convolution_pointer + idx + 2)] * kernel_weights_buffer[6] + 
                                                                      input_buffer[(convolution_pointer + idx + 3)] * kernel_weights_buffer[7] + 
                                                                      bias;
            end
            increment_pointer_phase <= 1;
        end else begin
            if (convolution_pointer >= (OUTPUT_BUFFER_SIZE + PADDING - CONVOLUTE_AT_ONCE)) begin
                output_buffer_valid <= 1;
                convolution_pointer <= PADDING;
            end else begin
                convolution_pointer <= convolution_pointer + CONVOLUTE_AT_ONCE;
            end
            increment_pointer_phase <= 0;
        end

    end else begin 
        case (cmd)
            0: begin 
                convolution_pointer <= PADDING;
            end 
            1: begin
                input_buffer[address    ] <= inp1[31:24];
                input_buffer[address + 1] <= inp1[23:16];
                input_buffer[address + 2] <= inp1[15: 8];
                input_buffer[address + 3] <= inp1[7 : 0];
            end
            2: begin
                kernel_weights_buffer[address    ] <= inp1[31:24];
                kernel_weights_buffer[address + 1] <= inp1[23:16];
                kernel_weights_buffer[address + 2] <= inp1[15: 8];
                kernel_weights_buffer[address + 3] <= inp1[7 : 0];
            end
            3: begin
                ret[31:24] <= output_buffer[address    ];
                ret[23:16] <= output_buffer[address + 1];
                ret[15: 8] <= output_buffer[address + 2];
                ret[7 : 0] <= output_buffer[address + 3];
            end
            4: begin
                ret <= OUTPUT_BUFFER_SIZE;
            end
            5: begin
                output_buffer_valid <= 0;
                convolution_pointer <= PADDING;
                increment_pointer_phase <= 0;
            end
            6: begin
                ret[31:24] <= input_buffer[address    ];
                ret[23:16] <= input_buffer[address + 1];
                ret[15: 8] <= input_buffer[address + 2];
                ret[7 : 0] <= input_buffer[address + 3];
            end
            7: begin
                ret[31:24] <= kernel_weights_buffer[address    ];
                ret[23:16] <= kernel_weights_buffer[address + 1];
                ret[15: 8] <= kernel_weights_buffer[address + 2];
                ret[7 : 0] <= kernel_weights_buffer[address + 3];
            end
            8: begin
                bias <= inp0;
            end
        endcase
    end
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
  // localparam InputOffset = $signed(9'd128);
  reg signed [8:0] input_offset = 128;
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
