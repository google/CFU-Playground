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
  input      [9:0]    cmd_payload_function_id,
  input      [31:0]   cmd_payload_inputs_0,
  input      [31:0]   cmd_payload_inputs_1,
  output              rsp_valid,
  input               rsp_ready,
  output     [31:0]   rsp_payload_outputs_0,
  input               reset,
  input               clk,
  output    [13:0]    port0_addr,
  output    [13:0]    port1_addr,
  output    [13:0]    port2_addr,
  output    [13:0]    port3_addr,
  input     [31:0]    port0_din,
  input     [31:0]    port1_din,
  input     [31:0]    port2_din,
  input     [31:0]    port3_din,
);

  reg cmd_valid_delay;
  always @(posedge clk) if (rsp_ready) cmd_valid_delay <= cmd_valid;

  // one clcok latency on the memory access
  assign rsp_valid = cmd_valid_delay;
  assign cmd_ready = rsp_ready;

  // spam address to all banks
  assign port0_addr = cmd_payload_inputs_1;
  assign port1_addr = cmd_payload_inputs_1;
  assign port2_addr = cmd_payload_inputs_1;
  assign port3_addr = cmd_payload_inputs_1;

  // pick result
  reg [1:0] bank_sel;
  always @(posedge clk) if (rsp_ready) bank_sel <= cmd_payload_inputs_0;
  assign rsp_payload_outputs_0 = bank_sel[1] ? (bank_sel[0] ? port3_din : port2_din)
                                             : (bank_sel[0] ? port1_din : port0_din);


endmodule
