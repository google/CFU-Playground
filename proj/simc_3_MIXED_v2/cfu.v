module Cfu (
  input               cmd_valid,
  output              cmd_ready,
  input      [9:0]    cmd_payload_function_id,
  input      [31:0]   cmd_payload_inputs_0,
  input      [31:0]   cmd_payload_inputs_1,
  output reg          rsp_valid,
  input               rsp_ready,
  output reg [31:0]   rsp_payload_outputs_0,
  input               reset,
  input               clk
);
  // localparam InputOffset = $signed(9'd128);
  reg signed [8:0] input_offset = 128;
  
  wire [6:0] funct7;
  assign funct7 = cmd_payload_function_id[9:3];

  // SIMD multiply step:
  wire signed [15:0] prod_0, prod_1, prod_2, prod_3;
  assign prod_0 =  ($signed(cmd_payload_inputs_0[7 : 0]) + input_offset)
                  * $signed(cmd_payload_inputs_1[7 : 0]);
  assign prod_1 =  ($signed(cmd_payload_inputs_0[15: 8]) + input_offset)
                  * $signed(cmd_payload_inputs_1[15: 8]);
  assign prod_2 =  ($signed(cmd_payload_inputs_0[23:16]) + input_offset)
                  * $signed(cmd_payload_inputs_1[23:16]);
  assign prod_3 =  ($signed(cmd_payload_inputs_0[31:24]) + input_offset)
                  * $signed(cmd_payload_inputs_1[31:24]);

  wire signed [31:0] sum_prods;
  assign sum_prods = prod_0 + prod_1 + prod_2 + prod_3;

  // Only not ready for a command when we have a response.
  assign cmd_ready = ~rsp_valid;

  always @(posedge clk) begin
    if (reset) begin
      rsp_payload_outputs_0 <= 32'b0;
      rsp_valid <= 1'b0;
    end else if (rsp_valid) begin
      // Waiting to hand off response to CPU.
      rsp_valid <= ~rsp_ready;
    end else if (cmd_valid) begin
      rsp_valid <= 1'b1;
      // Accumulate step:
      if (funct7 == 0) begin
        rsp_payload_outputs_0 <= rsp_payload_outputs_0 + sum_prods;
      end else if (funct7 == 1) begin
        rsp_payload_outputs_0 <= 32'b0;
      end else if (funct7 == 2) begin
        input_offset <= cmd_payload_inputs_0;
      end else begin
        rsp_payload_outputs_0 <= input_offset;
      end
      // rsp_payload_outputs_0 <= |cmd_payload_function_id[9:3]
      //     ? 32'b0
      //     : rsp_payload_outputs_0 + sum_prods;
    end
  end
endmodule