/*
 * Copyright 2021 The CFU-Playground Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef CFU_H
#define CFU_H

#include <stdint.h>

#include "riscv.h"
#include "software_cfu.h"

/* riscv.h defines a macro:

    #define opcode_R(opcode, funct3, funct7, rs1, rs2)

   that returns at 32b value.  The opcode must be "CUSTOM0" (also defined in
   riscv.h).

   'func3' is used as functionID sent to the CFU.

*/

// =============== Access the custom instruction

// generic name for each custom instruction - via hardware
#define cfu_op_hw(funct3, funct7, rs1, rs2) \
  opcode_R(CUSTOM0, funct3, funct7, (rs1), (rs2))
#define cfu_op0_hw(funct7, rs1, rs2) cfu_op_hw(0, funct7, rs1, rs2)
#define cfu_op1_hw(funct7, rs1, rs2) cfu_op_hw(1, funct7, rs1, rs2)
#define cfu_op2_hw(funct7, rs1, rs2) cfu_op_hw(2, funct7, rs1, rs2)
#define cfu_op3_hw(funct7, rs1, rs2) cfu_op_hw(3, funct7, rs1, rs2)
#define cfu_op4_hw(funct7, rs1, rs2) cfu_op_hw(4, funct7, rs1, rs2)
#define cfu_op5_hw(funct7, rs1, rs2) cfu_op_hw(5, funct7, rs1, rs2)
#define cfu_op6_hw(funct7, rs1, rs2) cfu_op_hw(6, funct7, rs1, rs2)
#define cfu_op7_hw(funct7, rs1, rs2) cfu_op_hw(7, funct7, rs1, rs2)

// generic name for each custom instruction - via software
#define cfu_op_sw(funct3, funct7, rs1, rs2) \
  software_cfu(funct3, funct7, rs1, rs2)
#define cfu_op0_sw(funct7, rs1, rs2) cfu_op_sw(0, funct7, rs1, rs2)
#define cfu_op1_sw(funct7, rs1, rs2) cfu_op_sw(1, funct7, rs1, rs2)
#define cfu_op2_sw(funct7, rs1, rs2) cfu_op_sw(2, funct7, rs1, rs2)
#define cfu_op3_sw(funct7, rs1, rs2) cfu_op_sw(3, funct7, rs1, rs2)
#define cfu_op4_sw(funct7, rs1, rs2) cfu_op_sw(4, funct7, rs1, rs2)
#define cfu_op5_sw(funct7, rs1, rs2) cfu_op_sw(5, funct7, rs1, rs2)
#define cfu_op6_sw(funct7, rs1, rs2) cfu_op_sw(6, funct7, rs1, rs2)
#define cfu_op7_sw(funct7, rs1, rs2) cfu_op_sw(7, funct7, rs1, rs2)

// generic name for each custom instruction - switchable
#define cfu_op0(funct7, rs1, rs2) cfu_op(0, funct7, rs1, rs2)
#define cfu_op1(funct7, rs1, rs2) cfu_op(1, funct7, rs1, rs2)
#define cfu_op2(funct7, rs1, rs2) cfu_op(2, funct7, rs1, rs2)
#define cfu_op3(funct7, rs1, rs2) cfu_op(3, funct7, rs1, rs2)
#define cfu_op4(funct7, rs1, rs2) cfu_op(4, funct7, rs1, rs2)
#define cfu_op5(funct7, rs1, rs2) cfu_op(5, funct7, rs1, rs2)
#define cfu_op6(funct7, rs1, rs2) cfu_op(6, funct7, rs1, rs2)
#define cfu_op7(funct7, rs1, rs2) cfu_op(7, funct7, rs1, rs2)

// =============== Switch HW vs SW

#ifdef CFU_SOFTWARE_DEFINED
#define cfu_op(funct3, funct7, rs1, rs2) cfu_op_sw(funct3, funct7, rs1, rs2)
#else
#define cfu_op(funct3, funct7, rs1, rs2) cfu_op_hw(funct3, funct7, rs1, rs2)
#endif

#endif  // CFU_H