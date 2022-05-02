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
  input               clk
);

  reg [31:0] count;
  reg [31:0] val;
  reg [31:0] val2;

  reg running;

  assign cmd_ready = !running;

  assign rsp_valid = running & (count == 0);

  always @(posedge clk) begin
      if (cmd_ready & cmd_valid) begin
          count <= cmd_payload_inputs_0;
          val <= 1;
          val2 <= 1;
          running <= 1'b1;
      end else if (count != 0) begin
          val <= val2;
          val2 <= val + val2;
          count <= count - 1;
      end else if (rsp_valid & rsp_ready) begin
          running <= 1'b0;
      end
  end

  assign rsp_payload_outputs_0 = rsp_valid ? val : 32'h00000000;


endmodule
