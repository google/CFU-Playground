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

// Optionally SIMD multiply and accumulate unit that adds constant offset to input_vals.

module mac (
  // Enable bits for SIMD and layer one input offset
  input logic layer_one_en,
  input logic simd_en,

  input logic [31:0] input_vals,
  input logic [31:0] filter_vals,
  input logic [31:0] curr_acc,

  output logic [31:0] out
);
  logic signed [8:0] InputOffest = layer_one_en ? -9'sd83 : 9'sd128;

  // Explicit rather than generated; saves LCs with current Yosys.
  logic signed [15:0] prod_0, prod_1, prod_2, prod_3;
  assign prod_0 = (signed'(input_vals[7:0])   + InputOffest) * signed'(filter_vals[7:0]);
  assign prod_1 = (signed'(input_vals[15:8])  + InputOffest) * signed'(filter_vals[15:8]);
  assign prod_2 = (signed'(input_vals[23:16]) + InputOffest) * signed'(filter_vals[23:16]);
  assign prod_3 = (signed'(input_vals[31:24]) + InputOffest) * signed'(filter_vals[31:24]);

  // Conditionally MAC or SIMD MAC.
  logic signed [31:0] sum_prods;
  always_comb begin
    sum_prods = prod_0;
    if (simd_en) begin
      sum_prods += prod_1 + prod_2 + prod_3;
    end
  end

  assign out = curr_acc + sum_prods;
endmodule
