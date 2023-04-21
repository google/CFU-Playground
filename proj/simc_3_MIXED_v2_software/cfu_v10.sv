// Difference from v9: 
//    Input and filter buffers are loaded
//    by 4 values at the time
module conv1d #(
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
  localparam PADDING = 4;  // (8 / 2)
  localparam MAX_INPUT_SIZE = 1024;
  localparam MAX_INPUT_CHANNELS = 128;
  localparam FILTER_LENGTH = 8;

  localparam SUM_AT_ONCE = 8;
  localparam BUFFERS_SIZE = FILTER_LENGTH * MAX_INPUT_CHANNELS;

  wire [INT32_SIZE-1:0] address = inp0;
  wire [INT32_SIZE-1:0] value = inp1;
  wire [INT32_SIZE-1:0] cur_buffer_size = FILTER_LENGTH * input_depth;

  // Buffers
  (* RAM_STYLE="BLOCK" *)
  reg signed [BYTE_SIZE-1:0] input_buffer[0:BUFFERS_SIZE - 1];

  (* RAM_STYLE="BLOCK" *)
  reg signed [BYTE_SIZE-1:0] filter_buffer[0:BUFFERS_SIZE - 1];

  // Parameters
  reg signed [INT32_SIZE-1:0] input_offset = 32'd0;
  // reg signed [INT32_SIZE-1:0] input_output_width = 32'd0;
  reg signed [INT32_SIZE-1:0] input_depth = 32'd0;

  // Computation related registers
  reg signed [INT32_SIZE-1:0] start_filter_x = 0;
  reg finished_work = 1'b1;
  reg update_address = 1'b0;
  reg [INT32_SIZE-1:0] filter_addr;
  reg [INT32_SIZE-1:0] input_addr;
  reg signed [INT32_SIZE-1:0] acc;

  always @(posedge clk) begin
    if (!finished_work) begin
      if (update_address) begin
        filter_addr <= filter_addr + SUM_AT_ONCE;
        if ((input_addr + SUM_AT_ONCE) >= cur_buffer_size) begin
          input_addr <= input_addr + SUM_AT_ONCE - cur_buffer_size;
        end else begin
          input_addr <= input_addr + SUM_AT_ONCE;
        end
        update_address <= 0;
      end else begin
        if (filter_addr >= cur_buffer_size) begin
          finished_work <= 1;
        end else begin
          acc <= acc + 
            filter_buffer[filter_addr     ] * (input_buffer[(input_addr     )] + input_offset) + 
            filter_buffer[filter_addr +  1] * (input_buffer[(input_addr +  1)] + input_offset) + 
            filter_buffer[filter_addr +  2] * (input_buffer[(input_addr +  2)] + input_offset) + 
            filter_buffer[filter_addr +  3] * (input_buffer[(input_addr +  3)] + input_offset) +
            filter_buffer[filter_addr +  4] * (input_buffer[(input_addr +  4)] + input_offset) + 
            filter_buffer[filter_addr +  5] * (input_buffer[(input_addr +  5)] + input_offset) + 
            filter_buffer[filter_addr +  6] * (input_buffer[(input_addr +  6)] + input_offset) + 
            filter_buffer[filter_addr +  7] * (input_buffer[(input_addr +  7)] + input_offset);

          // filter_buffer[filter_addr +  8] * (input_buffer[(input_addr +  8)] + input_offset) + 
          // filter_buffer[filter_addr +  9] * (input_buffer[(input_addr +  9)] + input_offset) + 
          // filter_buffer[filter_addr + 10] * (input_buffer[(input_addr + 10)] + input_offset) + 
          // filter_buffer[filter_addr + 11] * (input_buffer[(input_addr + 11)] + input_offset) +
          // filter_buffer[filter_addr + 12] * (input_buffer[(input_addr + 12)] + input_offset) + 
          // filter_buffer[filter_addr + 13] * (input_buffer[(input_addr + 13)] + input_offset) + 
          // filter_buffer[filter_addr + 14] * (input_buffer[(input_addr + 14)] + input_offset) + 
          // filter_buffer[filter_addr + 15] * (input_buffer[(input_addr + 15)] + input_offset);
        end
        update_address <= 1;
      end

    end

    case (cmd)
      // Initialize
      0: begin  // Reset module
        // Fill input with zeros
        ret <= BUFFERS_SIZE;
      end

      // Write buffers
      1: begin  // Write input buffer
        // if (address < BUFFERS_SIZE) begin
        input_buffer[address]   <= value[7:0];
        input_buffer[address+1] <= value[15:8];
        input_buffer[address+2] <= value[23:16];
        input_buffer[address+3] <= value[31:24];
        // end
      end
      2: begin  // Write filter buffer
        // if (address < BUFFERS_SIZE) begin
        filter_buffer[address]   <= value[7:0];
        filter_buffer[address+1] <= value[15:8];
        filter_buffer[address+2] <= value[23:16];
        filter_buffer[address+3] <= value[31:24];
        // end
      end

      // Write parameters
      3: begin
        input_offset <= value;
      end

      4: begin
        // input_output_width <= value;
        ret <= 0;
      end
      5: begin
        input_depth <= value;
      end

      6: begin  // Start computation
        acc <= 0;
        finished_work <= 0;
        update_address <= 0;
        filter_addr <= 0;
        input_addr <= start_filter_x * input_depth;
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
      10: begin
        // ret <= input_buffer[address];
        ret[7:0]   <= input_buffer[address];
        ret[15:8]  <= input_buffer[address+1];
        ret[23:16] <= input_buffer[address+2];
        ret[31:24] <= input_buffer[address+3];
      end
      11: begin
        ret[7:0]   <= filter_buffer[address];
        ret[15:8]  <= filter_buffer[address+1];
        ret[23:16] <= filter_buffer[address+2];
        ret[31:24] <= filter_buffer[address+3];
      end
      default: begin
        // $display("!!! DEFAULT case ");
        ret <= 0;
      end
    endcase
  end

endmodule

