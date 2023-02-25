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

  // Trivial handshaking for a combinational CFU
  assign rsp_valid = cmd_valid;
  assign cmd_ready = rsp_ready;

  // locally-stored width and height
  reg signed    [31:0]    w;
  reg signed    [31:0]    h;

  // treat inputs as signed values
  wire signed  [31:0] sin0 = cmd_payload_inputs_0;
  wire signed  [31:0] sin1 = cmd_payload_inputs_1;

  // calculate whether inputs are in box defined by (0,0,w,h)
  wire is_in = (sin0 >= 0) & (sin0 < w) &
               (sin1 >= 0) & (sin1 < h);

  // init --- store box width/height
  always @(posedge clk) begin
      if (cmd_valid & cmd_payload_function_id[0] == 1'b1) begin
          w = sin0;
          h = sin1;
      end
  end

  assign rsp_payload_outputs_0 = {31'd0, is_in};

endmodule
