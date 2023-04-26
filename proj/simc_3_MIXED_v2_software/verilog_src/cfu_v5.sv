`include "verilog_src/conf.sv"
`ifdef CFU_VERSION_5

module conv1d #(
    parameter BYTE_SIZE = 8,
    parameter INT32_SIZE = 32
)(
    input                         clk,
    input       [6:0]             cmd,
    input       [INT32_SIZE-1:0]  inp0,
    input       [INT32_SIZE-1:0]  inp1,
    output reg  [INT32_SIZE-1:0]  ret,
    output reg                    output_buffer_valid = 1
);
localparam PADDING = 4; // (8 / 2)
localparam MAX_INPUT_SIZE = 1024;
localparam MAX_INPUT_CHANNELS = 128;
localparam KERNEL_LENGTH = 8;


wire [INT32_SIZE-1:0] address = inp0;
wire [INT32_SIZE-1:0] value   = inp1;

// INPUT/OUTPUT BUFFER
reg [INT32_SIZE-1:0]       buffer_size;
// Input buffer has shape of 1024 x 128 
reg signed [BYTE_SIZE-1:0] input_buffer          [0:MAX_INPUT_SIZE * MAX_INPUT_CHANNELS - 1];
// kernel weights buffer has shape of 8 x 128 
reg signed [BYTE_SIZE-1:0] kernel_weights_buffer [0:KERNEL_LENGTH * MAX_INPUT_CHANNELS - 1];
// output buffer has a shape of 1024
reg signed [INT32_SIZE:0]  output_buffer         [0:MAX_INPUT_SIZE - 1];

reg signed [INT32_SIZE-1:0] input_offset = 32'd0;
reg signed [INT32_SIZE-1:0] output_offset = 32'd0;
reg signed [INT32_SIZE-1:0] output_activation_min = 32'd0;
reg signed [INT32_SIZE-1:0] output_activation_max = 32'd0;
reg signed [INT32_SIZE-1:0] output_depth = 32'd0;
reg signed [INT32_SIZE-1:0] input_output_width = 32'd0;
reg signed [INT32_SIZE-1:0] input_depth = 32'd0;

reg signed [INT32_SIZE-1:0] bias = 32'd0;
reg signed [INT32_SIZE-1:0] output_multiplier = 32'd0;
reg signed [INT32_SIZE-1:0] output_shift = 32'd0;

reg signed [BYTE_SIZE-1:0] input_val = 32'd0;
reg signed [BYTE_SIZE-1:0] filter_val = 32'd0;
wire signed [INT32_SIZE-1:0] test_val = filter_val * (input_val + input_offset);

reg signed [INT32_SIZE-1:0] acc = 0;
reg signed [INT32_SIZE-1:0] in_x_origin = 0;

always @(posedge clk) begin
    // Note that processor is little-endian
    case (cmd)
        // Initialize
        0: begin    // Reset module
            // Fill output with zeros
            for (reg [INT32_SIZE-1:0] out_x = 0; out_x < MAX_INPUT_SIZE; out_x = out_x + 1) begin
                output_buffer[out_x] = 0;
            end 

            // Fill input with zeros
            for (reg [INT32_SIZE-1:0] in_idx = 0; in_idx < MAX_INPUT_SIZE * MAX_INPUT_CHANNELS; in_idx = in_idx + 1) begin
                input_buffer[in_idx] = 0;
            end 

            // Fill kernel_weights_buffer with zeros
            for (reg [INT32_SIZE-1:0] kernel_idx = 0; kernel_idx < KERNEL_LENGTH * MAX_INPUT_CHANNELS; kernel_idx = kernel_idx + 1) begin
                kernel_weights_buffer[kernel_idx] = 0;
            end   
        end 
        1: begin
            input_val <= value;
        end
        2: begin
            filter_val <= value;
        end
        3: begin
            ret <= test_val;
        end
        4: begin
            ret[7:0] <= input_val;
        end
        5: begin
            ret[7:0] <= filter_val;
        end

        // Write buffers
        10: begin    // Write input buffer
            input_buffer[address] <= value[7:0];
        end
        11: begin    // Write kernel weights buffer
            // Note that processor is little-endian
            kernel_weights_buffer[address] <= value[7:0];
        end

        // Read buffers
        12: begin    // Read output buffer
            // Note that processor is little-endian
            ret <= output_buffer[address];
        end
        13: begin
            ret[7 : 0] <= input_buffer[address];
        end
        14: begin
            ret[7 : 0] <= kernel_weights_buffer[address];
        end
        15: begin    // Zero out output buffer
            for (reg [INT32_SIZE-1:0] out_x = 0; out_x < MAX_INPUT_SIZE; out_x = out_x + 1) begin
                output_buffer[out_x] = 0;
            end 
        end

        // Write parameters
        20: begin
            input_offset <= value;
        end

        21: begin
            output_offset <= value;
        end

        22: begin
            output_activation_min <= value;
        end
        23: begin
            output_activation_max <= value;
        end
        24: begin
            output_depth <= value;
        end
        25: begin
            input_output_width <= value;
        end
        26: begin
            input_depth <= value;
        end
        27: begin
            bias <= value;
        end
        28: begin
            output_multiplier <= value;
        end
        29: begin
            output_shift <= value;
        end

        40: begin    // Start computation
            // output_buffer_valid = 0;
            for (reg signed [INT32_SIZE-1:0] out_x = 0; out_x < MAX_INPUT_SIZE; out_x = out_x + 1) begin
                reg signed [INT32_SIZE-1:0] in_x_origin = out_x - 3;
                for (reg signed [INT32_SIZE-1:0] filter_x = 0; filter_x < 8; filter_x = filter_x + 1) begin
                    reg signed [INT32_SIZE-1:0] in_x = in_x_origin + filter_x;
                    for (reg signed [INT32_SIZE-1:0] in_channel = 0; in_channel < MAX_INPUT_CHANNELS; in_channel = in_channel + 1) begin
                        if ((in_x >= 0) && (in_x < input_output_width) && (in_channel < input_depth)) begin
                            output_buffer[out_x] += kernel_weights_buffer[filter_x * input_depth + in_channel]
                                    * (input_buffer[in_x * input_depth + in_channel] + input_offset);
                        end
                    end
                end
                output_buffer[out_x] += bias; 
            end
            // output_buffer_valid = 1;
        end

        41: begin 
            acc = 0;
            for (reg signed [INT32_SIZE-1:0] filter_x = 0; filter_x < 8; filter_x = filter_x + 1) begin
                reg signed [INT32_SIZE-1:0] in_x = in_x_origin + filter_x;
                for (reg signed [INT32_SIZE-1:0] in_channel = 0; in_channel < MAX_INPUT_CHANNELS; in_channel = in_channel + 1) begin
                    if ((in_x >= 0) && (in_x < input_output_width) && (in_channel < input_depth)) begin
                        acc += kernel_weights_buffer[filter_x * input_depth + in_channel] 
                            * (input_buffer[in_x * input_depth + in_channel] + input_offset);
                    end
                end
            end
        end
        42: begin
            in_x_origin <= value;
        end
        43: begin
            ret <= acc;
        end
    endcase
end
    
endmodule
`endif