`include "cfu.v"

module conv1d_tb;
reg clk;
reg [6:0]  cmd;
reg signed [31:0] inp0, inp1;
wire output_buffer_valid;
wire signed [31:0] ret;

initial begin
    $monitor ("cmd=%d | inp0=%h | inp1=%h | output_valid=%d | ret=%h", cmd, inp0, inp1, output_buffer_valid, ret);
    clk = 0;
    cmd = 0;
    inp0 = 0;
    inp1 = 0;

    // Test 1
    $display("==================== TEST 1 ! ====================");
    $display("Write data to input buffer");
    #15 cmd = 1; inp0 = 0; inp1 = 32'b0;    // left padding 
    #10 cmd = 1; inp0 = 1; inp1 = {8'd7, 8'd6, 8'd5, 8'd4};   
    #10 cmd = 1; inp0 = 2; inp1 = {8'd3, 8'd2, 8'd1, 8'd0};
    #10 cmd = 1; inp0 = 3; inp1 = 32'b0;    // right padding

    #10 $display("Read data from input buffer");
        cmd = 6; inp0 = 0;
    #10 cmd = 6; inp0 = 1;
    #10 cmd = 6; inp0 = 2;
    #10 cmd = 6; inp0 = 3;

    #10 $display("Write data to kernel weights buffer");
        cmd = 2; inp0 = 0; inp1 = {8'd2, 8'd2, 8'd2, 8'd2};   // write kernel_weights_buffer[0:3] = 7;
    #10 cmd = 2; inp0 = 1; inp1 = {8'd2, 8'd2, 8'd2, 8'd2};   // write kernel_weights_buffer[4:7] = 6;

    #10 $display("Read data from kernel weights buffer");
        cmd = 7; inp0 = 0;              // read  kernel weights buffer[0:3]
    #10 cmd = 7; inp0 = 1;              // read  kernel weights buffer[4:7]

    #10 $display("Set bias");
        cmd = 8; inp0 = 1;

    #10 $display("Read buffer size (should be 8)");
        cmd = 4; inp0 = 0; inp1 = 0;
    
    #10 $display("Start calculations.");
        cmd = 5;

    #30 $display("Read output");
        cmd = 3; inp0 = 0; inp1 = 0;
    #10 cmd = 3; inp0 = 1;

    #10 $finish;
end

always begin
    #5 clk = !clk;
end

conv1d U0 (
    .clk (clk),
    .cmd (cmd),
    .inp0 (inp0),
    .inp1 (inp1),
    .output_buffer_valid(output_buffer_valid),
    .ret (ret)
);

endmodule