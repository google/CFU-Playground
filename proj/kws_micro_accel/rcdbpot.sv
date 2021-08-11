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

// Rounding clamping divide by power of two. Given a dividend and a (negative)
// representation of an exponent in the range [9:5], output the dividend
// divided by 2^-negative_exponent correctly rounded up or down based on sign
// and remainder. Clamped to the range [127,-128] and shifted by -128.

module rcdbpot (
  input logic [31:0] dividend,
  input logic [31:0] negative_exponent,

  output logic [31:0] out
);
  logic [3:0] shift;
  logic signed [31:0] mask, remainder, threshold;

  always_comb begin
    // Weird ordering is most effective for LC usage.
    casez (negative_exponent[2:0])
      3'b111 : shift = 9;
      3'b?11 : shift = 5;
      3'b??1 : shift = 7;
      3'b?1? : shift = 6;
      default: shift = 8;
    endcase

    mask = ~({32{1'b1}} << shift);
    remainder = dividend & mask;
    threshold = (mask >> 1) + dividend[31];
    out = signed'(signed'(dividend) >>> shift);

    if (remainder > threshold) out += 1'b1;
    if (out[31]) out = 32'sd0;
    else if (|out[31:8]) out = 32'sd255;
    out -= 32'sd128;
  end
endmodule
