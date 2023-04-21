// `include "cfu_v10.sv"
`include "cfu_v11.sv"


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

  // conv1d CONV_1D (
  quant QUANT (
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
      // if (wait_reg) begin
      //   wait_reg <= 0;
      //   rsp_valid <= 0;
      // end else begin
      //   wait_reg <= 1;
      //   rsp_valid <= output_buffer_valid;
      // end

      rsp_valid <= output_buffer_valid;
    end
  end
endmodule



