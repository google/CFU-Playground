`include "quant.sv"

module quant_cfu #(
    parameter BYTE_SIZE  = 8,
    parameter INT32_SIZE = 32
) (
    input                       clk,
    input      [           6:0] cmd,
    input      [INT32_SIZE-1:0] inp0,
    input      [INT32_SIZE-1:0] inp1,
    output reg [INT32_SIZE-1:0] ret,
    output reg                  output_buffer_valid = 1
);

  reg signed [INT32_SIZE-1:0] bias;
  reg signed [INT32_SIZE-1:0] output_multiplier;
  reg signed [INT32_SIZE-1:0] output_shift;
  reg signed [INT32_SIZE-1:0] output_activation_min;
  reg signed [INT32_SIZE-1:0] output_activation_max;
  reg signed [INT32_SIZE-1:0] output_offset;

  reg signed [INT32_SIZE-1:0] quanted_acc;

  quant QUANT(
    .acc(inp1),

    .bias(bias),
    .output_multiplier(output_multiplier),
    .output_shift(output_shift),
    .output_activation_min(output_activation_min),
    .output_activation_max(output_activation_max),
    .output_offset(output_offset),

    .ret(quanted_acc)
  );


  always @(posedge clk) begin
    case (cmd)
      // Initialize
      0: begin  // Reset module
        ret <= 0;
      end

      1: begin
        bias <= inp1;
      end

      2: begin
        output_multiplier <= inp1;
      end

      3: begin
        output_shift <= inp1;
      end

      4: begin
        output_activation_min <= inp1;
      end

      5: begin
        output_activation_max <= inp1;
      end

      6: begin
        output_offset <= inp1;
      end

      7: begin
        ret <= quanted_acc;
      end

      default: begin
        // $display("!!! DEFAULT case ");
        ret <= 0;
      end
    endcase
  end

endmodule

