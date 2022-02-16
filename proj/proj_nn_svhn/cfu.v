`include "fp_mul.v"
module Cfu (
  input               cmd_valid,
  output              cmd_ready,
  input      [9:0]    cmd_payload_function_id,
  input      [31:0]   cmd_payload_inputs_0,
  input      [31:0]   cmd_payload_inputs_1,
  output reg          rsp_valid,
  input               rsp_ready,
  output reg [31:0]   rsp_payload_outputs_0,
  input               reset,
  input               clk
);

  localparam InputOffset = $signed(9'd128);

  //Output of fmul
  wire [31:0] fmul_prod;
  
  //Other wires or regs
  wire input_a_ack,input_b_ack;
  
  reg input_a_stb,input_b_stb,output_z_ack;
  
  multiplier fp_mul(.clk(clk), .input_a(cmd_payload_inputs_0), .input_b(cmd_payload_inputs_1), .input_a_stb(input_a_stb), .input_b_stb(input_b_stb), .rst(reset), .output_z(fmul_prod), 
  .output_z_stb(rsp_valid), .input_a_ack(input_a_ack), .input_b_ack(input_b_ack), .output_z_ack(output_z_ack));
  // Only not ready for a command when we have a response.
  assign cmd_ready = input_a_ack; // 1 when its in get_a state, else its going through some fp mult.

  always @(posedge clk) begin
    if (reset) begin
      rsp_payload_outputs_0 <= 32'b0;
      input_a_stb <= 0;
      input_b_stb <= 0;
    //  rsp_valid <= 1'b0;
    
    //If rsp is done and ready to ship out fp mul prod
    end else if (rsp_valid) begin
    //  rsp_valid <= ~rsp_ready;
    rsp_payload_outputs_0 <= cmd_payload_function_id[9:3]    ? 32'b0     : fmul_prod;
    // Now acknowledege z output is received.
    output_z_ack <= 1;
    //$display("rsp_payload_outputs_0 %f\n",rsp_payload_outputs_0);
    
      //Once the hw knows it has a valid cmd inp., execute fmult.
    end else if (cmd_valid) begin
      //Valid command so ack correct inps sent to fp_mul
      input_a_stb <= 1;
      input_b_stb <= 1;
    end
    //if(rsp_payload_outputs_0!=0) begin
    //end
  end
endmodule

