// No write_at_once
// Uses buffer of width 32
// Uses quant 2
// Async writing to computation
`include "verilog_src/conf.sv"
`ifdef CFU_VERSION_14
`include "quant_v2.sv"

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

  // localparam SUM_AT_ONCE = 1;
  // localparam SUM_AT_ONCE = 2;
  // localparam SUM_AT_ONCE = 4;
  // localparam SUM_AT_ONCE = 8;
  // localparam SUM_AT_ONCE = 16;
  // localparam SUM_AT_ONCE = 24;
  localparam SUM_AT_ONCE = 32;
  // localparam SUM_AT_ONCE = 64;
  localparam BUFFERS_SIZE = KERNEL_LENGTH * MAX_INPUT_CHANNELS;
  localparam INPUT_BUFFER_SIZE = (BUFFERS_SIZE + MAX_INPUT_CHANNELS) / 4;
  localparam FILTER_BUFFER_SIZE = BUFFERS_SIZE / 4;

  wire [INT32_SIZE-1:0] address = inp0;
  wire [INT32_SIZE-1:0] value = inp1;
  wire [INT32_SIZE-1:0] cur_kernel_buffer_size = KERNEL_LENGTH * input_depth;
  wire [INT32_SIZE-1:0] cur_input_buffer_size = (async_writing) ? cur_kernel_buffer_size + input_depth : cur_kernel_buffer_size;
  // wire [INT32_SIZE-1:0] cur_input_buffer_size = cur_kernel_buffer_size;

  // Buffers
  (* RAM_STYLE="BLOCK" *)
  reg signed [INT32_SIZE-1:0] input_buffer[0:INPUT_BUFFER_SIZE - 1];

  (* RAM_STYLE="BLOCK" *)
  reg signed [INT32_SIZE-1:0] filter_buffer[0:FILTER_BUFFER_SIZE - 1];

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

  reg async_writing = 0;


  // Computation related registers
  reg signed [INT32_SIZE-1:0] start_filter_x = 0;
  reg finished_work = 1'b1;
  reg update_address = 1'b0;
  reg [INT32_SIZE-1:0] kernel_addr;
  reg [INT32_SIZE-1:0] input_addr;
  reg signed [INT32_SIZE-1:0] acc;

  reg waiting_for_quant = 0;
  reg start_quant = 0;
  wire quant_done;

  quant QUANT (
      .clk(clk),
      .acc(acc),

      .start(start_quant),
      .ret_valid(quant_done),

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
        if (waiting_for_quant) begin
          start_quant <= 0;
          if (quant_done) begin

            // if (input_depth == 32) begin
              // $display("<<<< acc after quant: %d, before quant: %d ", quanted_acc, acc);
            // end

            finished_work <= 1;
            waiting_for_quant <= 0;
          end
        end else begin
          if (update_address) begin
            kernel_addr <= kernel_addr + SUM_AT_ONCE;
            if ((input_addr + SUM_AT_ONCE) >= cur_input_buffer_size) begin
              input_addr <= input_addr + SUM_AT_ONCE - cur_input_buffer_size;
            end else begin
              input_addr <= input_addr + SUM_AT_ONCE;
            end
            update_address <= 0;
          end else begin
            if (kernel_addr >= cur_kernel_buffer_size) begin
              // $display(">>>> acc before quant: %d", acc);
              waiting_for_quant <= 1;
              start_quant <= 1;
              // finished_work <= 1;
            end else begin
                // $display("input_addr: %d, cur_kernel_buffer_size: %d", input_addr, cur_input_buffer_size);
                // $display("acc += \n (%d * (%d + %d)) +\n (%d * (%d + %d)) +\n (%d * (%d + %d)) +\n (%d * (%d + %d)) +\n (%d * (%d + %d)) +\n (%d * (%d + %d)) +\n (%d * (%d + %d)) +\n (%d * (%d + %d));", 
                //   $signed(filter_buffer[kernel_addr / 4    ][ 7: 0]), $signed(input_buffer[(input_addr / 4    )][ 7: 0]), input_offset, 
                //   $signed(filter_buffer[kernel_addr / 4    ][15: 8]), $signed(input_buffer[(input_addr / 4    )][15: 8]), input_offset,
                //   $signed(filter_buffer[kernel_addr / 4    ][23:16]), $signed(input_buffer[(input_addr / 4    )][23:16]), input_offset, 
                //   $signed(filter_buffer[kernel_addr / 4    ][31:24]), $signed(input_buffer[(input_addr / 4    )][31:24]), input_offset,
                //   $signed(filter_buffer[kernel_addr / 4 + 1][ 7: 0]), $signed(input_buffer[(input_addr / 4 + 1)][ 7: 0]), input_offset, 
                //   $signed(filter_buffer[kernel_addr / 4 + 1][15: 8]), $signed(input_buffer[(input_addr / 4 + 1)][15: 8]), input_offset, 
                //   $signed(filter_buffer[kernel_addr / 4 + 1][23:16]), $signed(input_buffer[(input_addr / 4 + 1)][23:16]), input_offset, 
                //   $signed(filter_buffer[kernel_addr / 4 + 1][31:24]), $signed(input_buffer[(input_addr / 4 + 1)][31:24]), input_offset
                // );
              acc <= acc + 
                $signed(filter_buffer[kernel_addr / 4    ][ 7: 0]) * ($signed(input_buffer[(input_addr / 4    )][ 7: 0]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4    ][15: 8]) * ($signed(input_buffer[(input_addr / 4    )][15: 8]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4    ][23:16]) * ($signed(input_buffer[(input_addr / 4    )][23:16]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4    ][31:24]) * ($signed(input_buffer[(input_addr / 4    )][31:24]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4 + 1][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 1)][ 7: 0]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 1][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 1)][15: 8]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 1][23:16]) * ($signed(input_buffer[(input_addr / 4 + 1)][23:16]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 1][31:24]) * ($signed(input_buffer[(input_addr / 4 + 1)][31:24]) + input_offset) +

                $signed(filter_buffer[kernel_addr / 4 + 2][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 2)][ 7: 0]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 2][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 2)][15: 8]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4 + 2][23:16]) * ($signed(input_buffer[(input_addr / 4 + 2)][23:16]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 2][31:24]) * ($signed(input_buffer[(input_addr / 4 + 2)][31:24]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4 + 3][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 3)][ 7: 0]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 3][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 3)][15: 8]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 3][23:16]) * ($signed(input_buffer[(input_addr / 4 + 3)][23:16]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 3][31:24]) * ($signed(input_buffer[(input_addr / 4 + 3)][31:24]) + input_offset) +

                $signed(filter_buffer[kernel_addr / 4 + 4][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 4)][ 7: 0]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 4][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 4)][15: 8]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4 + 4][23:16]) * ($signed(input_buffer[(input_addr / 4 + 4)][23:16]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 4][31:24]) * ($signed(input_buffer[(input_addr / 4 + 4)][31:24]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4 + 5][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 5)][ 7: 0]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 5][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 5)][15: 8]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 5][23:16]) * ($signed(input_buffer[(input_addr / 4 + 5)][23:16]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 5][31:24]) * ($signed(input_buffer[(input_addr / 4 + 5)][31:24]) + input_offset) +

                $signed(filter_buffer[kernel_addr / 4 + 6][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 6)][ 7: 0]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 6][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 6)][15: 8]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4 + 6][23:16]) * ($signed(input_buffer[(input_addr / 4 + 6)][23:16]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 6][31:24]) * ($signed(input_buffer[(input_addr / 4 + 6)][31:24]) + input_offset) +
                $signed(filter_buffer[kernel_addr / 4 + 7][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 7)][ 7: 0]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 7][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 7)][15: 8]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 7][23:16]) * ($signed(input_buffer[(input_addr / 4 + 7)][23:16]) + input_offset) + 
                $signed(filter_buffer[kernel_addr / 4 + 7][31:24]) * ($signed(input_buffer[(input_addr / 4 + 7)][31:24]) + input_offset);

                // $signed(filter_buffer[kernel_addr / 4 + 8][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 8)][ 7: 0]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 + 8][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 8)][15: 8]) + input_offset) +
                // $signed(filter_buffer[kernel_addr / 4 + 8][23:16]) * ($signed(input_buffer[(input_addr / 4 + 8)][23:16]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 + 8][31:24]) * ($signed(input_buffer[(input_addr / 4 + 8)][31:24]) + input_offset) +
                // $signed(filter_buffer[kernel_addr / 4 + 9][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 9)][ 7: 0]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 + 9][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 9)][15: 8]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 + 9][23:16]) * ($signed(input_buffer[(input_addr / 4 + 9)][23:16]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 + 9][31:24]) * ($signed(input_buffer[(input_addr / 4 + 9)][31:24]) + input_offset) +

                // $signed(filter_buffer[kernel_addr / 4 +10][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 +10)][ 7: 0]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +10][15: 8]) * ($signed(input_buffer[(input_addr / 4 +10)][15: 8]) + input_offset) +
                // $signed(filter_buffer[kernel_addr / 4 +10][23:16]) * ($signed(input_buffer[(input_addr / 4 +10)][23:16]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +10][31:24]) * ($signed(input_buffer[(input_addr / 4 +10)][31:24]) + input_offset) +
                // $signed(filter_buffer[kernel_addr / 4 +11][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 +11)][ 7: 0]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +11][15: 8]) * ($signed(input_buffer[(input_addr / 4 +11)][15: 8]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +11][23:16]) * ($signed(input_buffer[(input_addr / 4 +11)][23:16]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +11][31:24]) * ($signed(input_buffer[(input_addr / 4 +11)][31:24]) + input_offset) +

                // $signed(filter_buffer[kernel_addr / 4 +12][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 +12)][ 7: 0]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +12][15: 8]) * ($signed(input_buffer[(input_addr / 4 +12)][15: 8]) + input_offset) +
                // $signed(filter_buffer[kernel_addr / 4 +12][23:16]) * ($signed(input_buffer[(input_addr / 4 +12)][23:16]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +12][31:24]) * ($signed(input_buffer[(input_addr / 4 +12)][31:24]) + input_offset) +
                // $signed(filter_buffer[kernel_addr / 4 +13][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 +13)][ 7: 0]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +13][15: 8]) * ($signed(input_buffer[(input_addr / 4 +13)][15: 8]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +13][23:16]) * ($signed(input_buffer[(input_addr / 4 +13)][23:16]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +13][31:24]) * ($signed(input_buffer[(input_addr / 4 +13)][31:24]) + input_offset) +

                // $signed(filter_buffer[kernel_addr / 4 +14][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 +14)][ 7: 0]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +14][15: 8]) * ($signed(input_buffer[(input_addr / 4 +14)][15: 8]) + input_offset) +
                // $signed(filter_buffer[kernel_addr / 4 +14][23:16]) * ($signed(input_buffer[(input_addr / 4 +14)][23:16]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +14][31:24]) * ($signed(input_buffer[(input_addr / 4 +14)][31:24]) + input_offset) +
                // $signed(filter_buffer[kernel_addr / 4 +15][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 +15)][ 7: 0]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +15][15: 8]) * ($signed(input_buffer[(input_addr / 4 +15)][15: 8]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +15][23:16]) * ($signed(input_buffer[(input_addr / 4 +15)][23:16]) + input_offset) + 
                // $signed(filter_buffer[kernel_addr / 4 +15][31:24]) * ($signed(input_buffer[(input_addr / 4 +15)][31:24]) + input_offset);

            end
            update_address <= 1;
          end
        end
      end

      case (cmd)
        // Initialize
        0: begin  // Reset module
          // Fill input with zeros
          ret <= SUM_AT_ONCE;
        end

        // Write buffers
        1: begin  // Write input buffer
          input_buffer[address/4] <= value;
        end
        2: begin  // Write kernel weights buffer
          filter_buffer[address/4] <= value;
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
          kernel_addr <= 0;
          input_addr <= start_filter_x * input_depth;
          // $display("cur_kernel_buffer_size: %d", cur_kernel_buffer_size);
          // $display("Start filter x: %d", start_filter_x);
          // $display("input buffer: \n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d",
          // // $display("input buffer: \n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b",
          //          $signed(input_buffer[0][7:0]),   $signed(input_buffer[0][15:8]), $signed(input_buffer[0][23:16]), $signed(input_buffer[0][31:24]),
          //          $signed(input_buffer[1][7:0]),   $signed(input_buffer[1][15:8]), $signed(input_buffer[1][23:16]), $signed(input_buffer[1][31:24]),
          //          $signed(input_buffer[2][7:0]),   $signed(input_buffer[2][15:8]), $signed(input_buffer[2][23:16]), $signed(input_buffer[2][31:24]),
          //          $signed(input_buffer[3][7:0]),   $signed(input_buffer[3][15:8]), $signed(input_buffer[3][23:16]), $signed(input_buffer[3][31:24]),
          //          $signed(input_buffer[4][7:0]),   $signed(input_buffer[4][15:8]), $signed(input_buffer[4][23:16]), $signed(input_buffer[4][31:24]),
          //          $signed(input_buffer[5][7:0]),   $signed(input_buffer[5][15:8]), $signed(input_buffer[5][23:16]), $signed(input_buffer[5][31:24]),
          //          $signed(input_buffer[6][7:0]),   $signed(input_buffer[6][15:8]), $signed(input_buffer[6][23:16]), $signed(input_buffer[6][31:24]),
          //          $signed(input_buffer[7][7:0]),   $signed(input_buffer[7][15:8]), $signed(input_buffer[7][23:16]), $signed(input_buffer[7][31:24]) 
          //          );
          // $display("filter buffer: \n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d\n%d - %d - %d - %d",
          // // $display("filter buffer: \n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b\n%b - %b - %b - %b",
          //          $signed(filter_buffer[0][7:0]),   $signed(filter_buffer[0][15:8]), $signed(filter_buffer[0][23:16]), $signed(filter_buffer[0][31:24]),
          //          $signed(filter_buffer[1][7:0]),   $signed(filter_buffer[1][15:8]), $signed(filter_buffer[1][23:16]), $signed(filter_buffer[1][31:24]),
          //          $signed(filter_buffer[2][7:0]),   $signed(filter_buffer[2][15:8]), $signed(filter_buffer[2][23:16]), $signed(filter_buffer[2][31:24]),
          //          $signed(filter_buffer[3][7:0]),   $signed(filter_buffer[3][15:8]), $signed(filter_buffer[3][23:16]), $signed(filter_buffer[3][31:24]),
          //          $signed(filter_buffer[4][7:0]),   $signed(filter_buffer[4][15:8]), $signed(filter_buffer[4][23:16]), $signed(filter_buffer[4][31:24]),
          //          $signed(filter_buffer[5][7:0]),   $signed(filter_buffer[5][15:8]), $signed(filter_buffer[5][23:16]), $signed(filter_buffer[5][31:24]),
          //          $signed(filter_buffer[6][7:0]),   $signed(filter_buffer[6][15:8]), $signed(filter_buffer[6][23:16]), $signed(filter_buffer[6][31:24]),
          //          $signed(filter_buffer[7][7:0]),   $signed(filter_buffer[7][15:8]), $signed(filter_buffer[7][23:16]), $signed(filter_buffer[7][31:24]) 
          //          );
          // $display("acc0=%d", 
          //       $signed(filter_buffer[0][ 7: 0]) * ($signed(input_buffer[0][ 7: 0]) + input_offset) + 
          //       $signed(filter_buffer[0][15: 8]) * ($signed(input_buffer[0][15: 8]) + input_offset) +
          //       $signed(filter_buffer[0][23:16]) * ($signed(input_buffer[0][23:16]) + input_offset) + 
          //       $signed(filter_buffer[0][31:24]) * ($signed(input_buffer[0][31:24]) + input_offset) +
          //       $signed(filter_buffer[1][ 7: 0]) * ($signed(input_buffer[1][ 7: 0]) + input_offset) + 
          //       $signed(filter_buffer[1][15: 8]) * ($signed(input_buffer[1][15: 8]) + input_offset) + 
          //       $signed(filter_buffer[1][23:16]) * ($signed(input_buffer[1][23:16]) + input_offset) + 
          //       $signed(filter_buffer[1][31:24]) * ($signed(input_buffer[1][31:24]) + input_offset) + 

          //       $signed(filter_buffer[2][ 7: 0]) * ($signed(input_buffer[2][ 7: 0]) + input_offset) + 
          //       $signed(filter_buffer[2][15: 8]) * ($signed(input_buffer[2][15: 8]) + input_offset) +
          //       $signed(filter_buffer[2][23:16]) * ($signed(input_buffer[2][23:16]) + input_offset) + 
          //       $signed(filter_buffer[2][31:24]) * ($signed(input_buffer[2][31:24]) + input_offset) +
          //       $signed(filter_buffer[3][ 7: 0]) * ($signed(input_buffer[3][ 7: 0]) + input_offset) + 
          //       $signed(filter_buffer[3][15: 8]) * ($signed(input_buffer[3][15: 8]) + input_offset) + 
          //       $signed(filter_buffer[3][23:16]) * ($signed(input_buffer[3][23:16]) + input_offset) + 
          //       $signed(filter_buffer[3][31:24]) * ($signed(input_buffer[3][31:24]) + input_offset)
          //   );
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

        // Quant parameters
        10: begin
          bias <= inp1;
        end
        11: begin
          output_multiplier <= inp1;
        end
        12: begin
          output_shift <= inp1;
        end
        13: begin
          output_activation_min <= inp1;
        end
        14: begin
          output_activation_max <= inp1;
        end
        15: begin
          output_offset <= inp1;
        end
        16: begin
          // $display("current input buffer size: %d, input_depth: %d", cur_input_buffer_size, input_depth);
          async_writing <= value;
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
