// Copyright 2021 The CFU-Playground Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

`include "mac.sv"
`include "rcdbpot.sv"
`include "rdh.sv"

module Cfu (
  input logic clk,
  input logic reset,

  // RISC-V assembly inputs ({funct7, funct3}, rs1, and rs2)
  input logic [9:0]  cmd_payload_function_id,
  input logic [31:0] cmd_payload_inputs_0,
  input logic [31:0] cmd_payload_inputs_1,

  // CFU output signals
  output logic [31:0] rsp_payload_outputs_0,

  // CFU <---> CPU handshaking
  input  logic cmd_valid,
  output logic cmd_ready,
  output logic rsp_valid,
  input  logic rsp_ready
);
  // Optionally SIMD multiply and accumulate with input offset.
  logic [31:0] mac_output;
  mac kws_mac (
      .layer_one_en(cmd_payload_function_id[4]),
      .simd_en(cmd_payload_function_id[3]),
      .input_vals(cmd_payload_inputs_0),
      .filter_vals(cmd_payload_inputs_1),
      .curr_acc(rsp_payload_outputs_0),
      .out(mac_output)
  );

  // Rounding doubling high 32 bits.
  logic [31:0] rdh_output;
  rdh kws_rdh (
      .top(cmd_payload_inputs_0),
      .bottom(cmd_payload_inputs_1),
      .out(rdh_output)
  );

  // Rounding clamping divide by power of two.
  logic [31:0] rcdbpot_output;
  rcdbpot kws_rcdbpot (
      .dividend(rsp_payload_outputs_0),
      .negative_exponent(cmd_payload_inputs_1),
      .out(rcdbpot_output)
  );

  // Output selection (one-hot encoding).
  always_ff @(posedge clk) begin
    if (cmd_valid) begin
      casez (cmd_payload_function_id[2:0])
        3'b??1 : rsp_payload_outputs_0 <= mac_output;
        3'b?1? : rsp_payload_outputs_0 <= rdh_output;
        3'b1?? : rsp_payload_outputs_0 <= rcdbpot_output;
        default: rsp_payload_outputs_0 <= '0;
      endcase
    end
  end

  // Only not ready for a command when we have a response.
  assign cmd_ready = ~rsp_valid;

  // Single cycle CFU handshaking.
  always_ff @(posedge clk) begin
    if (reset) begin
      rsp_valid <= '0;
    end else if (rsp_valid) begin
      // Waiting to hand off response to CPU.
      rsp_valid <= ~rsp_ready;
    end else if (cmd_valid) begin
      rsp_valid <= '1;
    end
  end
endmodule
