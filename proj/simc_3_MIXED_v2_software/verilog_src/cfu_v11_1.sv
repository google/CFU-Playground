// Differs from v9 by quantation module.
`include "verilog_src/conf.sv"
`ifdef CFU_VERSION_11_1

`include "quant.sv"

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

  localparam SUM_AT_ONCE = 8;
  localparam BUFFERS_SIZE = KERNEL_LENGTH * MAX_INPUT_CHANNELS;

  wire [INT32_SIZE-1:0] address = inp0;
  wire [INT32_SIZE-1:0] value = inp1;
  wire [INT32_SIZE-1:0] cur_buffer_size = KERNEL_LENGTH * input_depth;

  // Buffers
  (* RAM_STYLE="BLOCK" *)
  reg signed [BYTE_SIZE-1:0] input_buffer[0:BUFFERS_SIZE - 1];

  (* RAM_STYLE="BLOCK" *)
  reg signed [BYTE_SIZE-1:0] filter_buffer[0:BUFFERS_SIZE - 1];

  // Parameters
  reg signed [INT32_SIZE-1:0] input_offset = 32'd0;
  // reg signed [INT32_SIZE-1:0] input_output_width = 32'd0;
  reg signed [INT32_SIZE-1:0] input_depth = 32'd0;

  // Quanting info
  reg signed [INT32_SIZE-1:0] bias;
  reg signed [INT32_SIZE-1:0] output_multiplier;
  reg signed [INT32_SIZE-1:0] output_shift;
  reg signed [INT32_SIZE-1:0] output_activation_min;
  reg signed [INT32_SIZE-1:0] output_activation_max;
  reg signed [INT32_SIZE-1:0] output_offset;

  wire signed [INT32_SIZE-1:0] quanted_acc;

  reg signed [BYTE_SIZE-1:0] sum_input_0;
  reg signed [BYTE_SIZE-1:0] sum_input_1;
  reg signed [BYTE_SIZE-1:0] sum_input_2;
  reg signed [BYTE_SIZE-1:0] sum_input_3;
  reg signed [BYTE_SIZE-1:0] sum_input_4;
  reg signed [BYTE_SIZE-1:0] sum_input_5;
  reg signed [BYTE_SIZE-1:0] sum_input_6;
  reg signed [BYTE_SIZE-1:0] sum_input_7;

  reg signed [BYTE_SIZE-1:0] sum_filter_0;
  reg signed [BYTE_SIZE-1:0] sum_filter_1;
  reg signed [BYTE_SIZE-1:0] sum_filter_2;
  reg signed [BYTE_SIZE-1:0] sum_filter_3;
  reg signed [BYTE_SIZE-1:0] sum_filter_4;
  reg signed [BYTE_SIZE-1:0] sum_filter_5;
  reg signed [BYTE_SIZE-1:0] sum_filter_6;
  reg signed [BYTE_SIZE-1:0] sum_filter_7;

  // Computation related registers
  reg signed [INT32_SIZE-1:0] start_filter_x = 0;
  reg finished_work = 1'b1;
  // reg update_address = 1'b0;
  reg load_data = 1'b0;
  reg [INT32_SIZE-1:0] kernel_addr;
  reg [INT32_SIZE-1:0] input_addr;
  reg signed [INT32_SIZE-1:0] acc;

  quant QUANT (
      .acc(acc),

      .bias(bias),
      .output_multiplier(output_multiplier),
      .output_shift(output_shift),
      .output_activation_min(output_activation_min),
      .output_activation_max(output_activation_max),
      .output_offset(output_offset),

      .ret(quanted_acc)
  );



  always @(posedge clk) begin
    if (en) begin
      if (!finished_work) begin
        if (load_data) begin
          sum_input_0  <= input_buffer[input_addr];
          sum_input_1  <= input_buffer[input_addr+1];
          sum_input_2  <= input_buffer[input_addr+2];
          sum_input_3  <= input_buffer[input_addr+3];
          sum_input_4  <= input_buffer[input_addr+4];
          sum_input_5  <= input_buffer[input_addr+5];
          sum_input_6  <= input_buffer[input_addr+6];
          sum_input_7  <= input_buffer[input_addr+7];

          sum_filter_0 <= filter_buffer[kernel_addr];
          sum_filter_1 <= filter_buffer[kernel_addr+1];
          sum_filter_2 <= filter_buffer[kernel_addr+2];
          sum_filter_3 <= filter_buffer[kernel_addr+3];
          sum_filter_4 <= filter_buffer[kernel_addr+4];
          sum_filter_5 <= filter_buffer[kernel_addr+5];
          sum_filter_6 <= filter_buffer[kernel_addr+6];
          sum_filter_7 <= filter_buffer[kernel_addr+7];

          load_data    <= 0;
        end else begin
          if (kernel_addr >= cur_buffer_size) begin
            finished_work <= 1;
          end else begin
            acc <= acc + 
                 sum_filter_0 * (sum_input_0 + input_offset) +
                 sum_filter_1 * (sum_input_1 + input_offset) +
                 sum_filter_2 * (sum_input_2 + input_offset) +
                 sum_filter_3 * (sum_input_3 + input_offset) +
                 sum_filter_4 * (sum_input_4 + input_offset) +
                 sum_filter_5 * (sum_input_5 + input_offset) +
                 sum_filter_6 * (sum_input_6 + input_offset) +
                 sum_filter_7 * (sum_input_7 + input_offset);

            kernel_addr <= kernel_addr + SUM_AT_ONCE;
            if ((input_addr + SUM_AT_ONCE) >= cur_buffer_size) begin
              input_addr <= input_addr + SUM_AT_ONCE - cur_buffer_size;
            end else begin
              input_addr <= input_addr + SUM_AT_ONCE;
            end
          end
          load_data <= 1;
        end

      end

      // if (!finished_work) begin
      //   if (update_address) begin
      //     kernel_addr <= kernel_addr + SUM_AT_ONCE;
      //     if ((input_addr + SUM_AT_ONCE) >= cur_buffer_size) begin
      //       input_addr <= input_addr + SUM_AT_ONCE - cur_buffer_size;
      //     end else begin
      //       input_addr <= input_addr + SUM_AT_ONCE;
      //     end
      //     update_address <= 0;
      //   end else begin
      //     if (kernel_addr >= cur_buffer_size) begin
      //       finished_work <= 1;
      //     end else begin
      //       acc <= acc + 
      //       filter_buffer[kernel_addr     ] * (input_buffer[(input_addr    )] + input_offset) + 
      //       filter_buffer[kernel_addr +  1] * (input_buffer[(input_addr + 1)] + input_offset) + 
      //       filter_buffer[kernel_addr +  2] * (input_buffer[(input_addr + 2)] + input_offset) + 
      //       filter_buffer[kernel_addr +  3] * (input_buffer[(input_addr + 3)] + input_offset) +
      //       filter_buffer[kernel_addr +  4] * (input_buffer[(input_addr + 4)] + input_offset) + 
      //       filter_buffer[kernel_addr +  5] * (input_buffer[(input_addr + 5)] + input_offset) + 
      //       filter_buffer[kernel_addr +  6] * (input_buffer[(input_addr + 6)] + input_offset) + 
      //       filter_buffer[kernel_addr +  7] * (input_buffer[(input_addr + 7)] + input_offset);
      //     end
      //     update_address <= 1;
      //   end

      // end

      case (cmd)
        // Initialize
        0: begin  // Reset module
          // Fill input with zeros
          ret <= BUFFERS_SIZE;
        end

        // Write buffers
        1: begin  // Write input buffer
          // if (address < BUFFERS_SIZE) begin
          input_buffer[address] <= value[7:0];
          // end
        end
        2: begin  // Write kernel weights buffer
          // if (address < BUFFERS_SIZE) begin
          filter_buffer[address] <= value[7:0];
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
          // update_address <= 0;
          load_data <= 1;
          kernel_addr <= 0;
          input_addr <= start_filter_x * input_depth;
        end

        7: begin  // get acumulator
          // ret <= acc;
          ret <= quanted_acc;
        end
        8: begin  // Write start x in input ring buffer 
          start_filter_x <= value;
        end
        9: begin  // Check if computation is done
          ret <= finished_work;
        end

        // 10: begin
        //   ret <= input_buffer[address];
        // end
        // 11: begin
        //   ret <= filter_buffer[address];
        // end

        // Quant parameters
        12: begin
          bias <= inp1;
        end
        13: begin
          output_multiplier <= inp1;
        end
        14: begin
          output_shift <= inp1;
        end
        15: begin
          output_activation_min <= inp1;
        end
        16: begin
          output_activation_max <= inp1;
        end
        17: begin
          output_offset <= inp1;
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
