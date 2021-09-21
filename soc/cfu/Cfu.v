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
  output     [31:0]   rsp_payload_outputs_0,
  input               clk,
  input               reset
);

  assign rsp_valid = cmd_valid;
  assign cmd_ready = rsp_ready;

  //  byte sum (unsigned)
  wire [31:0] cfu0;
  assign cfu0[31:0] =  cmd_payload_inputs_0[7:0]   + cmd_payload_inputs_1[7:0] +
                       cmd_payload_inputs_0[15:8]  + cmd_payload_inputs_1[15:8] +
                       cmd_payload_inputs_0[23:16] + cmd_payload_inputs_1[23:16] +
                       cmd_payload_inputs_0[31:24] + cmd_payload_inputs_1[31:24];

  // byte swap
  wire [31:0] cfu1;
  assign cfu1[31:24] =     cmd_payload_inputs_0[7:0];
  assign cfu1[23:16] =     cmd_payload_inputs_0[15:8];
  assign cfu1[15:8] =      cmd_payload_inputs_0[23:16];
  assign cfu1[7:0] =       cmd_payload_inputs_0[31:24];

  // bit reverse
  wire [31:0] cfu2;
  genvar n;
  generate
      for (n=0; n<32; n=n+1) begin
          assign cfu2[n] =     cmd_payload_inputs_0[31-n];
      end
  endgenerate


  // select output
  assign rsp_payload_outputs_0 = cmd_payload_function_id[1] ? cfu2 :
                                      ( cmd_payload_function_id[0] ? cfu1 : cfu0);


endmodule
