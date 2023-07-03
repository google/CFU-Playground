// Should have better timings because of:
//  1. accumulation of accumulations

// No write_at_once
// Uses buffer of width 32
// Uses quant 2
// Async writing to computation
`include "verilog_src/conf.sv"
`ifdef CFU_VERSION_14_1
`include "verilog_src/quant_v2.sv"

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

  // localparam SUM_AT_ONCE = 4;
  // localparam SUM_AT_ONCE = 8;
  // localparam SUM_AT_ONCE = 16;
  // localparam SUM_AT_ONCE = 24;
  localparam SUM_AT_ONCE = 32;
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

  // Somputation states
  reg waiting_for_quant = 0;
  reg accumulation = 0;
  reg acc_accs = 0;

  reg signed [INT32_SIZE-1:0] acc00;
  reg signed [INT32_SIZE-1:0] acc01;
  reg signed [INT32_SIZE-1:0] acc02;
  reg signed [INT32_SIZE-1:0] acc03;
  reg signed [INT32_SIZE-1:0] acc04;
  reg signed [INT32_SIZE-1:0] acc05;
  reg signed [INT32_SIZE-1:0] acc06;
  reg signed [INT32_SIZE-1:0] acc07;
  reg signed [INT32_SIZE-1:0] acc08;
  reg signed [INT32_SIZE-1:0] acc09;
  reg signed [INT32_SIZE-1:0] acc10;
  reg signed [INT32_SIZE-1:0] acc11;
  reg signed [INT32_SIZE-1:0] acc12;
  reg signed [INT32_SIZE-1:0] acc13;
  reg signed [INT32_SIZE-1:0] acc14;
  reg signed [INT32_SIZE-1:0] acc15;

  reg signed [INT32_SIZE-1:0] acc16;
  reg signed [INT32_SIZE-1:0] acc17;
  reg signed [INT32_SIZE-1:0] acc18;
  reg signed [INT32_SIZE-1:0] acc19;
  reg signed [INT32_SIZE-1:0] acc20;
  reg signed [INT32_SIZE-1:0] acc21;
  reg signed [INT32_SIZE-1:0] acc22;
  reg signed [INT32_SIZE-1:0] acc23;
  reg signed [INT32_SIZE-1:0] acc24;
  reg signed [INT32_SIZE-1:0] acc25;
  reg signed [INT32_SIZE-1:0] acc26;
  reg signed [INT32_SIZE-1:0] acc27;
  reg signed [INT32_SIZE-1:0] acc28;
  reg signed [INT32_SIZE-1:0] acc29;
  reg signed [INT32_SIZE-1:0] acc30;
  reg signed [INT32_SIZE-1:0] acc31;


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
        end
        if (acc_accs) begin
          // $display("acc0: %d, acc1: %d", acc00, acc01);
          acc <=  acc00 + acc01 + acc02 + acc03 + acc04 + acc05 + acc06 + acc07 + 
                  acc08 + acc09 + acc10 + acc11 + acc12 + acc13 + acc14 + acc15 +  
                  acc16 + acc17 + acc18 + acc19 + acc20 + acc21 + acc22 + acc23 + 
                  acc24 + acc25 + acc26 + acc27 + acc28 + acc29 + acc30 + acc31;
          acc_accs <= 0;
          waiting_for_quant <= 1;
          start_quant <= 1;
        end
        if (accumulation) begin
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
              acc_accs <= 1;
              accumulation <= 0;

              // waiting_for_quant <= 1;
              // start_quant <= 1;
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
                // $display("acc0 += %d",  $signed(filter_buffer[kernel_addr / 4    ][ 7: 0]) * ($signed(input_buffer[(input_addr / 4    )][ 7: 0]) + input_offset));
                // $display("acc1 += %d",  $signed(filter_buffer[kernel_addr / 4    ][15: 8]) * ($signed(input_buffer[(input_addr / 4    )][15: 8]) + input_offset));
                acc00 <= acc00 + $signed(filter_buffer[kernel_addr / 4    ][ 7: 0]) * ($signed(input_buffer[(input_addr / 4    )][ 7: 0]) + input_offset); 
                acc01 <= acc01 + $signed(filter_buffer[kernel_addr / 4    ][15: 8]) * ($signed(input_buffer[(input_addr / 4    )][15: 8]) + input_offset);
                acc02 <= acc02 + $signed(filter_buffer[kernel_addr / 4    ][23:16]) * ($signed(input_buffer[(input_addr / 4    )][23:16]) + input_offset); 
                acc03 <= acc03 + $signed(filter_buffer[kernel_addr / 4    ][31:24]) * ($signed(input_buffer[(input_addr / 4    )][31:24]) + input_offset);
                acc04 <= acc04 + $signed(filter_buffer[kernel_addr / 4 + 1][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 1)][ 7: 0]) + input_offset); 
                acc05 <= acc05 + $signed(filter_buffer[kernel_addr / 4 + 1][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 1)][15: 8]) + input_offset); 
                acc06 <= acc06 + $signed(filter_buffer[kernel_addr / 4 + 1][23:16]) * ($signed(input_buffer[(input_addr / 4 + 1)][23:16]) + input_offset); 
                acc07 <= acc07 + $signed(filter_buffer[kernel_addr / 4 + 1][31:24]) * ($signed(input_buffer[(input_addr / 4 + 1)][31:24]) + input_offset);
                acc08 <= acc08 + $signed(filter_buffer[kernel_addr / 4 + 2][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 2)][ 7: 0]) + input_offset); 
                acc09 <= acc09 + $signed(filter_buffer[kernel_addr / 4 + 2][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 2)][15: 8]) + input_offset);
                acc10 <= acc10 + $signed(filter_buffer[kernel_addr / 4 + 2][23:16]) * ($signed(input_buffer[(input_addr / 4 + 2)][23:16]) + input_offset); 
                acc11 <= acc11 + $signed(filter_buffer[kernel_addr / 4 + 2][31:24]) * ($signed(input_buffer[(input_addr / 4 + 2)][31:24]) + input_offset);
                acc12 <= acc12 + $signed(filter_buffer[kernel_addr / 4 + 3][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 3)][ 7: 0]) + input_offset); 
                acc13 <= acc13 + $signed(filter_buffer[kernel_addr / 4 + 3][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 3)][15: 8]) + input_offset); 
                acc14 <= acc14 + $signed(filter_buffer[kernel_addr / 4 + 3][23:16]) * ($signed(input_buffer[(input_addr / 4 + 3)][23:16]) + input_offset); 
                acc15 <= acc15 + $signed(filter_buffer[kernel_addr / 4 + 3][31:24]) * ($signed(input_buffer[(input_addr / 4 + 3)][31:24]) + input_offset);


                acc16 <= acc16 + $signed(filter_buffer[kernel_addr / 4 + 4][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 4)][ 7: 0]) + input_offset) + 
                acc17 <= acc17 + $signed(filter_buffer[kernel_addr / 4 + 4][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 4)][15: 8]) + input_offset) +
                acc18 <= acc18 + $signed(filter_buffer[kernel_addr / 4 + 4][23:16]) * ($signed(input_buffer[(input_addr / 4 + 4)][23:16]) + input_offset) + 
                acc19 <= acc19 + $signed(filter_buffer[kernel_addr / 4 + 4][31:24]) * ($signed(input_buffer[(input_addr / 4 + 4)][31:24]) + input_offset) +
                acc20 <= acc20 + $signed(filter_buffer[kernel_addr / 4 + 5][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 5)][ 7: 0]) + input_offset) + 
                acc21 <= acc21 + $signed(filter_buffer[kernel_addr / 4 + 5][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 5)][15: 8]) + input_offset) + 
                acc22 <= acc22 + $signed(filter_buffer[kernel_addr / 4 + 5][23:16]) * ($signed(input_buffer[(input_addr / 4 + 5)][23:16]) + input_offset) + 
                acc23 <= acc23 + $signed(filter_buffer[kernel_addr / 4 + 5][31:24]) * ($signed(input_buffer[(input_addr / 4 + 5)][31:24]) + input_offset) +
                acc24 <= acc24 + $signed(filter_buffer[kernel_addr / 4 + 6][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 6)][ 7: 0]) + input_offset) + 
                acc25 <= acc25 + $signed(filter_buffer[kernel_addr / 4 + 6][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 6)][15: 8]) + input_offset) +
                acc26 <= acc26 + $signed(filter_buffer[kernel_addr / 4 + 6][23:16]) * ($signed(input_buffer[(input_addr / 4 + 6)][23:16]) + input_offset) + 
                acc27 <= acc27 + $signed(filter_buffer[kernel_addr / 4 + 6][31:24]) * ($signed(input_buffer[(input_addr / 4 + 6)][31:24]) + input_offset) +
                acc28 <= acc28 + $signed(filter_buffer[kernel_addr / 4 + 7][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 7)][ 7: 0]) + input_offset) + 
                acc29 <= acc29 + $signed(filter_buffer[kernel_addr / 4 + 7][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 7)][15: 8]) + input_offset) + 
                acc30 <= acc30 + $signed(filter_buffer[kernel_addr / 4 + 7][23:16]) * ($signed(input_buffer[(input_addr / 4 + 7)][23:16]) + input_offset) + 
                acc31 <= acc31 + $signed(filter_buffer[kernel_addr / 4 + 7][31:24]) * ($signed(input_buffer[(input_addr / 4 + 7)][31:24]) + input_offset);

              // acc <= acc + 
              //   $signed(filter_buffer[kernel_addr / 4    ][ 7: 0]) * ($signed(input_buffer[(input_addr / 4    )][ 7: 0]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4    ][15: 8]) * ($signed(input_buffer[(input_addr / 4    )][15: 8]) + input_offset) +
              //   $signed(filter_buffer[kernel_addr / 4    ][23:16]) * ($signed(input_buffer[(input_addr / 4    )][23:16]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4    ][31:24]) * ($signed(input_buffer[(input_addr / 4    )][31:24]) + input_offset) +
              //   $signed(filter_buffer[kernel_addr / 4 + 1][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 1)][ 7: 0]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4 + 1][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 1)][15: 8]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4 + 1][23:16]) * ($signed(input_buffer[(input_addr / 4 + 1)][23:16]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4 + 1][31:24]) * ($signed(input_buffer[(input_addr / 4 + 1)][31:24]) + input_offset) +

              //   $signed(filter_buffer[kernel_addr / 4 + 2][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 2)][ 7: 0]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4 + 2][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 2)][15: 8]) + input_offset) +
              //   $signed(filter_buffer[kernel_addr / 4 + 2][23:16]) * ($signed(input_buffer[(input_addr / 4 + 2)][23:16]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4 + 2][31:24]) * ($signed(input_buffer[(input_addr / 4 + 2)][31:24]) + input_offset) +
              //   $signed(filter_buffer[kernel_addr / 4 + 3][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 3)][ 7: 0]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4 + 3][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 3)][15: 8]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4 + 3][23:16]) * ($signed(input_buffer[(input_addr / 4 + 3)][23:16]) + input_offset) + 
              //   $signed(filter_buffer[kernel_addr / 4 + 3][31:24]) * ($signed(input_buffer[(input_addr / 4 + 3)][31:24]) + input_offset);

              // $signed(filter_buffer[kernel_addr / 4 + 4][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 4)][ 7: 0]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 4][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 4)][15: 8]) + input_offset) +
              // $signed(filter_buffer[kernel_addr / 4 + 4][23:16]) * ($signed(input_buffer[(input_addr / 4 + 4)][23:16]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 4][31:24]) * ($signed(input_buffer[(input_addr / 4 + 4)][31:24]) + input_offset) +
              // $signed(filter_buffer[kernel_addr / 4 + 5][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 5)][ 7: 0]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 5][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 5)][15: 8]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 5][23:16]) * ($signed(input_buffer[(input_addr / 4 + 5)][23:16]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 5][31:24]) * ($signed(input_buffer[(input_addr / 4 + 5)][31:24]) + input_offset) +

              // $signed(filter_buffer[kernel_addr / 4 + 6][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 6)][ 7: 0]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 6][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 6)][15: 8]) + input_offset) +
              // $signed(filter_buffer[kernel_addr / 4 + 6][23:16]) * ($signed(input_buffer[(input_addr / 4 + 6)][23:16]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 6][31:24]) * ($signed(input_buffer[(input_addr / 4 + 6)][31:24]) + input_offset) +
              // $signed(filter_buffer[kernel_addr / 4 + 7][ 7: 0]) * ($signed(input_buffer[(input_addr / 4 + 7)][ 7: 0]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 7][15: 8]) * ($signed(input_buffer[(input_addr / 4 + 7)][15: 8]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 7][23:16]) * ($signed(input_buffer[(input_addr / 4 + 7)][23:16]) + input_offset) + 
              // $signed(filter_buffer[kernel_addr / 4 + 7][31:24]) * ($signed(input_buffer[(input_addr / 4 + 7)][31:24]) + input_offset);

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
          accumulation <= 1;
          update_address <= 0;
          kernel_addr <= 0;
          input_addr <= start_filter_x * input_depth;

          acc00 <= 0;
          acc01 <= 0;
          acc02 <= 0;
          acc03 <= 0;
          acc04 <= 0;
          acc05 <= 0;
          acc06 <= 0;
          acc07 <= 0;
          acc08 <= 0;
          acc09 <= 0;
          acc10 <= 0;
          acc11 <= 0;
          acc12 <= 0;
          acc13 <= 0;
          acc14 <= 0;
          acc15 <= 0;
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
