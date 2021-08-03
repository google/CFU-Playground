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
  input               cmd_valid,
  output              cmd_ready,
  input      [2:0]    cmd_payload_function_id,
  input      [31:0]   cmd_payload_inputs_0,
  input      [31:0]   cmd_payload_inputs_1,

  output              rsp_valid,
  input               rsp_ready,
  output              rsp_payload_response_ok,
  output     [31:0]   rsp_payload_outputs_0,

  input               reset,
  input               clk
);

  // Trivial handshaking for a combinational CFU
  assign rsp_valid = cmd_valid;
  assign cmd_ready = rsp_ready;
  assign rsp_payload_response_ok = 1'b1;

  // Convenience renaming
  wire [ 9:0] opc = cmd_payload_function_id;
  wire signed [31:0] in1 = cmd_payload_inputs_0;
  wire signed [31:0] in2 = cmd_payload_inputs_1;
  wire signed [31:0] out;
  assign rsp_payload_outputs_0 = out;


  //
  // The CFU computation
  //
  reg signed [31:0] input_offset;      // state
  reg signed [31:0] acc;               // state

  wire signed [31:0] filt_val = in1;
  wire signed [31:0] input_val = in2;

  wire signed [31:0] newacc = acc + (filt_val * (input_val + input_offset) );
  assign out = acc;

  always @(posedge clk) begin
    if (cmd_valid) begin
      if (opc[2:0] == 3'b000) begin
        input_offset <= in1;
      end else if (opc[2:0] == 3'b001) begin
        acc <= in1;
      end else if (opc[2:0] == 3'b010) begin
        acc <= newacc;
      end
    end
  end

endmodule
