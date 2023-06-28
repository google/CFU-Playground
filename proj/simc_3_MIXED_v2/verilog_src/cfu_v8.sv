`include "verilog_src/conf.sv"
`ifdef CFU_VERSION_8

module conv1d #(
    parameter BYTE_SIZE  = 8,
    parameter INT32_SIZE = 32
) (
    input                       clk,
    input                       en,
    input      [           6:0] cmd,
    input      [INT32_SIZE-1:0] inp0,
    input      [INT32_SIZE-1:0] inp1,
    output reg [INT32_SIZE-1:0] ret,
    output reg                  output_buffer_valid = 1
);
  localparam PADDING = 4;  // (8 / 2)
  localparam MAX_INPUT_SIZE = 1024;
  localparam MAX_INPUT_CHANNELS = 128;
  localparam KERNEL_LENGTH = 8;

  localparam BUFFERS_SIZE = KERNEL_LENGTH * MAX_INPUT_CHANNELS;
  localparam SUM_AT_ONCE = 8;
  localparam CLOCKS_TODO_JOB = BUFFERS_SIZE / SUM_AT_ONCE;


  wire [INT32_SIZE-1:0] address = inp0;
  wire [INT32_SIZE-1:0] value = inp1;

  // Buffers
  (* RAM_STYLE="BLOCK" *)
  reg signed [BYTE_SIZE-1:0] input_buffer[0:BUFFERS_SIZE - 1];

  (* RAM_STYLE="BLOCK" *)
  reg signed [BYTE_SIZE-1:0] kernel_weights_buffer[0:BUFFERS_SIZE - 1];

  // Parameters
  reg signed [INT32_SIZE-1:0] input_offset = 32'd0;
  reg signed [INT32_SIZE-1:0] input_output_width = 32'd0;
  reg signed [INT32_SIZE-1:0] input_depth = 32'd0;

  // Computation related registers
  reg signed [INT32_SIZE-1:0] start_filter_x = 0;
  reg finished_work = 1'b1;
  reg unsigned [INT32_SIZE-1:0] addr_counter = 0; // KERNEL_LENGTH * MAX_INPUT_CHANNELS = 8 * 128 = 1024 == 2**10
  reg signed [INT32_SIZE-1:0] acc = 0;

  always @(posedge clk) begin
    if (en) begin
      if (!finished_work) begin
        if (addr_counter >= BUFFERS_SIZE) begin
          finished_work = 1;
        end else begin
          acc <= acc + 
          kernel_weights_buffer[addr_counter     ] * (input_buffer[(addr_counter +      start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          kernel_weights_buffer[addr_counter +  1] * (input_buffer[(addr_counter +  1 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          kernel_weights_buffer[addr_counter +  2] * (input_buffer[(addr_counter +  2 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) +
          kernel_weights_buffer[addr_counter +  3] * (input_buffer[(addr_counter +  3 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          kernel_weights_buffer[addr_counter +  4] * (input_buffer[(addr_counter +  4 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) +
          kernel_weights_buffer[addr_counter +  5] * (input_buffer[(addr_counter +  5 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          kernel_weights_buffer[addr_counter +  6] * (input_buffer[(addr_counter +  6 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          kernel_weights_buffer[addr_counter +  7] * (input_buffer[(addr_counter +  7 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset);

          // kernel_weights_buffer[addr_counter +  8] * (input_buffer[(addr_counter +  8 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) +
          // kernel_weights_buffer[addr_counter +  9] * (input_buffer[(addr_counter +  9 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 10] * (input_buffer[(addr_counter + 10 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 11] * (input_buffer[(addr_counter + 11 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 12] * (input_buffer[(addr_counter + 12 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 13] * (input_buffer[(addr_counter + 13 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 14] * (input_buffer[(addr_counter + 14 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 15] * (input_buffer[(addr_counter + 15 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) +

          // kernel_weights_buffer[addr_counter + 16] * (input_buffer[(addr_counter + 16 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) +
          // kernel_weights_buffer[addr_counter + 17] * (input_buffer[(addr_counter + 17 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 18] * (input_buffer[(addr_counter + 18 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) +
          // kernel_weights_buffer[addr_counter + 19] * (input_buffer[(addr_counter + 19 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 20] * (input_buffer[(addr_counter + 20 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) +
          // kernel_weights_buffer[addr_counter + 21] * (input_buffer[(addr_counter + 21 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 22] * (input_buffer[(addr_counter + 22 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 23] * (input_buffer[(addr_counter + 23 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 

          // kernel_weights_buffer[addr_counter + 24] * (input_buffer[(addr_counter + 24 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) +
          // kernel_weights_buffer[addr_counter + 25] * (input_buffer[(addr_counter + 25 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 26] * (input_buffer[(addr_counter + 26 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 27] * (input_buffer[(addr_counter + 27 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 28] * (input_buffer[(addr_counter + 28 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 29] * (input_buffer[(addr_counter + 29 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 30] * (input_buffer[(addr_counter + 30 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset) + 
          // kernel_weights_buffer[addr_counter + 31] * (input_buffer[(addr_counter + 31 + start_filter_x * input_depth) % (8 * input_depth)] + input_offset);


          addr_counter = addr_counter + SUM_AT_ONCE;
        end


      end

      case (cmd)
        // Initialize
        0: begin  // Reset module
          // Fill input with zeros
        end

        // Write buffers
        1: begin  // Write input buffer
          input_buffer[address] <= value[7:0];
        end
        2: begin  // Write kernel weights buffer
          kernel_weights_buffer[address] <= value[7:0];
        end

        // Write parameters
        3: begin
          input_offset <= value;
        end

        4: begin
          input_output_width <= value;
        end
        5: begin
          input_depth <= value;
        end

        6: begin  // Start computation
          acc <= 0;
          finished_work = 0;
          addr_counter  = 0;
        end

        7: begin  // get acumulator
          ret <= acc;
        end
        8: begin  // Write start x in input ring buffer 
          start_filter_x <= value;
        end
        9: begin  // Check if computation is done
          ret <= finished_work;
        end
        default: begin
          // $display("!!! DEFAULT case ");
          ret <= 0;
        end
      endcase
    end
  end

endmodule
`endif
