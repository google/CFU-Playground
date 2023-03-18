`include "cfu.v"

// Testbench Code Goes here
module conv1d_tb;
reg clk;
reg [6:0]  cmd;
reg signed [31:0] inp0, inp1;
wire output_buffer_valid;
wire signed [31:0] ret;

/*
    Note: we write 4 values at the time, so address should be multiple of 4
*/
reg  [31:0] row;
reg  [31:0] col;
wire [31:0] input_address = row * 128 + col;
wire [31:0] kernel_address = input_address;

initial begin
    $monitor ("cmd=%d | inp0=%d | inp1=%h | output_valid=%d | ret=%h", cmd, inp0, inp1, output_buffer_valid, ret);
    clk = 0;
    cmd = 0;
    inp0 = 0;
    inp1 = 0;

    /*
        Input buffer has a size of 1024 x 128 = max_input_size * max_input_channels
        Let's write 8 values with 2 channels to the input buffer + 
            4 x 2 zero padding at beginning and end

        Kernel weights has a size of 8 x 128 = kernel_length * max_input_channels
        Let's write 8 values with 2 channels to the kernel weighrs buffer

        Input buffer:         Kernel buffer:     Expected output buffer:

        ^  00  00 .. 00 ^
        |  00  00 .. 00 |
        |  00  00 .. 00 |
        |  00  00 .. 00 |
        |  07  00 .. 00 |     ^ 02 01 .. 00 ^     | 50 |
        |  06  01 .. 00 |     | 02 01 .. 00 |     | 60 |
        |  05  02 .. 00 |     | 02 01 .. 00 |     | 69 |
        |  04  03 .. 00 |     | 02 01 .. 00 |     | 77 | 
        |  03  04 .. 00 |     | 02 01 .. 00 |     | 84 | 
        |  02  05 .. 00 |     | 02 01 .. 00 |     | 70 | 
        |  01  06 .. 00 |     | 02 01 .. 00 |     | 57 | 
        |  00  07 .. 00 |     v 02 01 .. 00 v     | 45 |   
        |  00  00 .. 00 |
        |  00  00 .. 00 |
        |  00  00 .. 00 |
        |  00  00 .. 00 |
        |  ..  ..       |
        |  ..  ..       |
        v  00        00 v
    
    */


    $display("Write data to input buffer");
    // Paddings at the beginning
    #15 cmd = 1; row = 0; col = 0; inp0 = input_address; inp1 = 0;
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = 0;
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = 0;
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = 0;

    // Input values
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd7, 8'd0, 8'd0, 8'd0};
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd6, 8'd1, 8'd0, 8'd0};
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd5, 8'd2, 8'd0, 8'd0};
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd4, 8'd3, 8'd0, 8'd0};
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd3, 8'd4, 8'd0, 8'd0};
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd2, 8'd5, 8'd0, 8'd0};
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd1, 8'd6, 8'd0, 8'd0};
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd0, 8'd7, 8'd0, 8'd0};

    // Paddings at the end
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = 0;
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = 0;
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = 0;
    #10 cmd = 1; row = row + 1; col = 0; inp0 = input_address; inp1 = 0;

    #10 $display("Read data from input buffer");
        cmd = 5; row = 4;       col = 0; inp0 = input_address;
    #10 cmd = 5; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 5; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 5; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 5; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 5; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 5; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 5; row = row + 1; col = 0; inp0 = input_address;

    #10 $display("Write data to kernel weights buffer");
        cmd = 2; row = 0;       col = 0; inp0 = input_address; inp1 = {8'd2, 8'd1, 8'd0, 8'd0};
    #10 cmd = 2; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd2, 8'd1, 8'd0, 8'd0};
    #10 cmd = 2; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd2, 8'd1, 8'd0, 8'd0};
    #10 cmd = 2; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd2, 8'd1, 8'd0, 8'd0};
    #10 cmd = 2; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd2, 8'd1, 8'd0, 8'd0};
    #10 cmd = 2; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd2, 8'd1, 8'd0, 8'd0};
    #10 cmd = 2; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd2, 8'd1, 8'd0, 8'd0};
    #10 cmd = 2; row = row + 1; col = 0; inp0 = input_address; inp1 = {8'd2, 8'd1, 8'd0, 8'd0};

    #10 $display("Read data from kernel weights buffer");
        cmd = 6; row = 0;       col = 0; inp0 = input_address;
    #10 cmd = 6; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 6; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 6; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 6; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 6; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 6; row = row + 1; col = 0; inp0 = input_address;
    #10 cmd = 6; row = row + 1; col = 0; inp0 = input_address;

    #10 $display("Set bias");
        cmd = 7; inp0 = 1;

    // #10 $display("Set input offset");
        // cmd = 8; inp0 = -1;

    #10 $display("Start calculations.");
        cmd = 4;

    #10 $display("Read output");
        cmd = 3; inp0 = 0;
    #10 cmd = 3; inp0 = 4;

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