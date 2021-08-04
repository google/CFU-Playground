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

module Cfu (
  input logic clk,
  input logic reset,

  // RISC-V assembly inputs ({funct7, funct3}, rs1, and rs2)
  input logic [9:0]  cmd_payload_function_id,
  input logic [31:0] cmd_payload_inputs_0,
  input logic [31:0] cmd_payload_inputs_1,

  // CFU output signals
  output logic        rsp_payload_response_ok,
  output logic [31:0] rsp_payload_outputs_0,

  // CFU <---> CPU handshaking
  input  logic cmd_valid,
  output logic cmd_ready,
  output logic rsp_valid,
  input  logic rsp_ready
);
  localparam logic signed [8:0] InputOffest = 9'd128;

  // Explicit rather than generated; saves LCs with current Yosys.
  logic signed [15:0] prod_0, prod_1, prod_2, prod_3;
  assign prod_0 = ( signed'(cmd_payload_inputs_0[7 :0 ]) + InputOffest)
                  * signed'(cmd_payload_inputs_1[7 :0 ]);
  assign prod_1 = ( signed'(cmd_payload_inputs_0[15:8 ]) + InputOffest)
                  * signed'(cmd_payload_inputs_1[15:8 ]);
  assign prod_2 = ( signed'(cmd_payload_inputs_0[23:16]) + InputOffest)
                  * signed'(cmd_payload_inputs_1[23:16]);
  assign prod_3 = ( signed'(cmd_payload_inputs_0[31:24]) + InputOffest)
                  * signed'(cmd_payload_inputs_1[31:24]);

  // Conditionally MAC or SIMD MAC.
  logic signed [31:0] sum_prods;
  always_comb begin
    if (cmd_payload_function_id[0]) begin
      sum_prods = prod_0;
    end else begin
      sum_prods = prod_0 + prod_1 + prod_2 + prod_3;
    end
  end

  // Only not ready for a command when we have a response.
  assign cmd_ready = ~rsp_valid;
  assign rsp_payload_response_ok = '1;

  // Handshaking and accumulation.
  always_ff @(posedge clk) begin
    if (reset) begin
      rsp_payload_outputs_0 <= '0;
      rsp_valid <= '0;
    end else if (rsp_valid) begin
      // Waiting to hand off response to CPU.
      rsp_valid <= ~rsp_ready;
    end else if (cmd_valid) begin
      rsp_valid <= '1;
      if (cmd_payload_function_id[3]) begin
        rsp_payload_outputs_0 <= 0;
      end else begin
        rsp_payload_outputs_0 <= sum_prods + rsp_payload_outputs_0;
      end
    end
  end
endmodule
