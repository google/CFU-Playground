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

#ifdef __cplusplus
extern "C" {
#endif

/* riscv.h defines a macro:

    #define opcode_R(opcode, funct3, funct7, rs1, rs2)

   that returns at 32b value.  The opcode must be "CUSTOM0" (also defined in
   riscv.h).

   'func3' is used as functionID sent to the CFU.

*/

// =============== Access the custom instruction

// generic name for each custom instruction
#define cfu_op0_hw(funct7, rs1, rs2) opcode_R(CUSTOM0, 0, funct7, (rs1), (rs2))
#define cfu_op1_hw(funct7, rs1, rs2) opcode_R(CUSTOM0, 1, funct7, (rs1), (rs2))
#define cfu_op2_hw(funct7, rs1, rs2) opcode_R(CUSTOM0, 2, funct7, (rs1), (rs2))
#define cfu_op3_hw(funct7, rs1, rs2) opcode_R(CUSTOM0, 3, funct7, (rs1), (rs2))
#define cfu_op4_hw(funct7, rs1, rs2) opcode_R(CUSTOM0, 4, funct7, (rs1), (rs2))
#define cfu_op5_hw(funct7, rs1, rs2) opcode_R(CUSTOM0, 5, funct7, (rs1), (rs2))
#define cfu_op6_hw(funct7, rs1, rs2) opcode_R(CUSTOM0, 6, funct7, (rs1), (rs2))
#define cfu_op7_hw(funct7, rs1, rs2) opcode_R(CUSTOM0, 7, funct7, (rs1), (rs2))

// generic name for each custom instruction
#define cfu_op0_sw(funct7, rs1, rs2) software_cfu(0, funct7, rs1, rs2)
#define cfu_op1_sw(funct7, rs1, rs2) software_cfu(1, funct7, rs1, rs2)
#define cfu_op2_sw(funct7, rs1, rs2) software_cfu(2, funct7, rs1, rs2)
#define cfu_op3_sw(funct7, rs1, rs2) software_cfu(3, funct7, rs1, rs2)
#define cfu_op4_sw(funct7, rs1, rs2) software_cfu(4, funct7, rs1, rs2)
#define cfu_op5_sw(funct7, rs1, rs2) software_cfu(5, funct7, rs1, rs2)
#define cfu_op6_sw(funct7, rs1, rs2) software_cfu(6, funct7, rs1, rs2)
#define cfu_op7_sw(funct7, rs1, rs2) software_cfu(7, funct7, rs1, rs2)

// =============== Switch HW vs SW

#ifdef CFU_SOFTWARE_DEFINED

#define cfu_op0(funct7, rs1, rs2) cfu_op0_sw(funct7, rs1, rs2)
#define cfu_op1(funct7, rs1, rs2) cfu_op1_sw(funct7, rs1, rs2)
#define cfu_op2(funct7, rs1, rs2) cfu_op2_sw(funct7, rs1, rs2)
#define cfu_op3(funct7, rs1, rs2) cfu_op3_sw(funct7, rs1, rs2)
#define cfu_op4(funct7, rs1, rs2) cfu_op4_sw(funct7, rs1, rs2)
#define cfu_op5(funct7, rs1, rs2) cfu_op5_sw(funct7, rs1, rs2)
#define cfu_op6(funct7, rs1, rs2) cfu_op6_sw(funct7, rs1, rs2)
#define cfu_op7(funct7, rs1, rs2) cfu_op7_sw(funct7, rs1, rs2)

#else

#define cfu_op0(funct7, rs1, rs2) cfu_op0_hw(funct7, (rs1), (rs2))
#define cfu_op1(funct7, rs1, rs2) cfu_op1_hw(funct7, (rs1), (rs2))
#define cfu_op2(funct7, rs1, rs2) cfu_op2_hw(funct7, (rs1), (rs2))
#define cfu_op3(funct7, rs1, rs2) cfu_op3_hw(funct7, (rs1), (rs2))
#define cfu_op4(funct7, rs1, rs2) cfu_op4_hw(funct7, (rs1), (rs2))
#define cfu_op5(funct7, rs1, rs2) cfu_op5_hw(funct7, (rs1), (rs2))
#define cfu_op6(funct7, rs1, rs2) cfu_op6_hw(funct7, (rs1), (rs2))
#define cfu_op7(funct7, rs1, rs2) cfu_op7_hw(funct7, (rs1), (rs2))

#endif

#ifdef __cplusplus
}
#endif
#endif  // CFU_H