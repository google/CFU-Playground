// Copyright 2021 The CFU-Playground Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <verilated.h>          // Defines common routines
#include <iostream>             // Need std::cout
#include <vector>
#include <tuple>

#include "Vcfu.h"               // From Verilating "cfu.v"

#if VM_TRACE
#include "verilated_vcd_c.h"
#endif

using namespace std;

Vcfu *cfu;                      // Instantiation of module

vluint64_t main_time = 0;       // Current simulation time
// This is a 64-bit integer to reduce wrap over issues and
// allow modulus.  This is in units of the timeprecision
// used in Verilog (or from --timescale-override)

double sc_time_stamp () {       // Called by $time in Verilog
    return main_time;           // converts to double, to match
                                // what SystemC does
}

const vector<pair<vector<int>,int>> test_vectors = {
    {{1, 10, 10}, 1},
    {{0, 10, 10}, 0},
    {{0, 0,   0}, 1},
    {{0, 1,   1}, 1},
    {{0, 10,  1}, 0},
    {{0, 1,  10}, 0},
    {{0, -1,  1}, 0},
    {{0, 1,  -1}, 0},
    {{0, -1, -1}, 0},
    {{1, 16, 16}, 1},
    {{0, 10, 10}, 1},
    {{0, 16, 16}, 0}
};

// CFU ports:
//  io_bus_cmd_valid
//  io_bus_cmd_ready,
//  io_bus_cmd_payload_function_id,
//  io_bus_cmd_payload_inputs_0,
//  io_bus_cmd_payload_inputs_1,
//  io_bus_rsp_valid,
//  io_bus_rsp_ready,
//  io_bus_rsp_payload_response_ok,
//  io_bus_rsp_payload_outputs_0,
//  clk,
//  rst,

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);   // Remember args

    cfu = new Vcfu;                       // Create instance

#if VM_TRACE
    Verilated::traceEverOn(true);         // Enable VCD trace
    VerilatedVcdC* tfp = new VerilatedVcdC;
    printf("Enable VCD tracing...\n");
    cfu->trace(tfp, 9);  // Trace 9 levels of hierarchy
    tfp->open("cfu.vcd");
#endif


    cfu->io_bus_cmd_valid = 0;            // Set inputs
    cfu->io_bus_cmd_payload_function_id = 0;
    cfu->io_bus_cmd_payload_inputs_0 = 0;
    cfu->io_bus_cmd_payload_inputs_1 = 0;
    cfu->io_bus_rsp_ready = 1;
    cfu->clk = 0;
    cfu->rst = 1;

    unsigned vec_num = 0;
    unsigned expected = 0;

    while (!Verilated::gotFinish()) {
#if VM_TRACE
        tfp->dump(main_time);
#endif
        if (main_time > 10) {
            cfu->rst = 0;   // Deassert reset
        }
        if ((main_time % 10) == 1) {
            cfu->clk = 1;       // Toggle clock
        }
        if ((main_time % 10) == 6) {
            cfu->clk = 0;
        }
        if ((main_time % 10) == 7) {
            if (expected != cfu->io_bus_rsp_payload_outputs_0) {
                printf("MISMATCH got 0x%08X, expected 0x%08X\n",
                    cfu->io_bus_rsp_payload_outputs_0, expected);
#if VM_TRACE
                tfp->close();
#endif
                exit(1);
            }
            if (vec_num == test_vectors.size()) break;
        }
        if (main_time >= 40 && (main_time % 10) == 0) {
          auto s = test_vectors[vec_num++];
          auto ins = s.first;
          unsigned out = s.second;
          cfu->io_bus_cmd_valid = 1;
          cfu->io_bus_cmd_payload_function_id = ins[0];
          cfu->io_bus_cmd_payload_inputs_0 = ins[1];
          cfu->io_bus_cmd_payload_inputs_1 = ins[2];
          expected = out;   // will be checked later
          printf("func #%d, in0 0x%08X, in1 0x%08X, expect %08X\n", ins[0], ins[1], ins[2], out);
        }
        cfu->eval();            // Evaluate model
        //cout << main_time << "  " << cfu->io_bus_rsp_payload_outputs_0 << endl;       // Read a output
        main_time++;            // Time passes...
        if (main_time > 1000) break;
    }

    cfu->final();               // Done simulating
#if VM_TRACE
    tfp->close();
#endif
    delete cfu;

    // No errors
    printf("FINISHED\n");
    return(0);
}
