// `include "cfu_full_v9.v"
// `include "cfu_full_v111.v"

`include "verilog_src/cfu_v0.sv"
`include "verilog_src/cfu_v5.sv"
`include "verilog_src/cfu_v6.sv"
`include "verilog_src/cfu_v7.sv"
`include "verilog_src/cfu_v8.sv"
`include "verilog_src/cfu_v9.sv"
`include "verilog_src/cfu_v11.sv"
`include "verilog_src/cfu_v11_1.sv"
`include "verilog_src/cfu_v11_2.sv"
`include "verilog_src/cfu_v12.sv"
`include "verilog_src/cfu_v12_05.sv"
`include "verilog_src/cfu_v12_1.sv"
`include "verilog_src/cfu_v12_2.sv"
`include "verilog_src/cfu_v12_3.sv"
`include "verilog_src/cfu_v13.sv"
`include "verilog_src/cfu_v13_2.sv"
`include "verilog_src/cfu_v14.sv"
`include "verilog_src/cfu_v14_1.sv"


module Cfu (
    input              cmd_valid,
    output             cmd_ready,
    input       [ 9:0] cmd_payload_function_id,
    input       [31:0] cmd_payload_inputs_0,
    input       [31:0] cmd_payload_inputs_1,
    output reg         rsp_valid,
    input              rsp_ready,
    output wire [31:0] rsp_payload_outputs_0,
    input              reset,
    input              clk
);
  wire output_buffer_valid;

  wire [6:0] funct7;
  assign funct7 = cmd_payload_function_id[9:3];
  // reg wait_reg = 0;
  wire [31:0] ret;

  conv1d CONV_1D (
      .clk(clk),
      .en(cmd_valid),
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
