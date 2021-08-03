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
  wire [31:0] in1 = cmd_payload_inputs_0;
  wire [31:0] in2 = cmd_payload_inputs_1;
  wire [31:0] out;
  assign rsp_payload_outputs_0 = out;


  //
  // The CFU computation
  //
  assign out = (opc[2:0] == 0) ? 
                        ((in1 > in2) ? (in1-in2) : (in2-in1))    // abs(in1-in2)
               :
                        (in1 * 4 + in2);


endmodule
