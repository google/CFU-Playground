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


#include "riscv.h"

/* riscv.h defines a macro:

    #define opcode_R(opcode, funct3, funct7, rs1, rs2)

   that returns at 32b value.  The opcode must be "CUSTOM0" (also defined in riscv.h).

   'func3' is used as functionID sent to the CFU.

   For this CFU, this is the interpretation of funct3:

   funct3       operation       inputs used
   --------------------------------------------------------
   3'bx00       byte sum     (rs1 and rs2)
   3'bx01       byte swap    (rs1 only, ignores rs2)
   3'bx1x       bit reverse  (rs1 only, ignores rs2)

*/

// =============== Access the custom instruction

// generic name for each custom instruction
#define cfu_op0_hw(rs1, rs2)  opcode_R(CUSTOM0, 0, 0, (rs1), (rs2))
#define cfu_op1_hw(rs1, rs2)  opcode_R(CUSTOM0, 1, 0, (rs1), (rs2))
#define cfu_op2_hw(rs1, rs2)  opcode_R(CUSTOM0, 2, 0, (rs1), (rs2))
#define cfu_op3_hw(rs1, rs2)  opcode_R(CUSTOM0, 3, 0, (rs1), (rs2))

// useful name for each custom instruction
#define cfu_byte_sum_hw(rs1, rs2)  opcode_R(CUSTOM0, 0, 0, (rs1), (rs2))
#define cfu_byte_swap_hw(rs1, rs2)  opcode_R(CUSTOM0, 1, 0, (rs1), (rs2))
#define cfu_bit_reverse_hw(rs1, rs2)  opcode_R(CUSTOM0, 2, 0, (rs1), (rs2))
#define cfu_fib_hw(rs1, rs2)  opcode_R(CUSTOM0, 3, 0, (rs1), (rs2))




// =============== Software (C implementation of custom instructions)

uint32_t Cfu(uint32_t functionid, uint32_t rs1, uint32_t rs2);

// generic name for each custom instruction
#define cfu_op0_sw(rs1, rs2)  Cfu(0, rs1, rs2)
#define cfu_op1_sw(rs1, rs2)  Cfu(1, rs1, rs2)
#define cfu_op2_sw(rs1, rs2)  Cfu(2, rs1, rs2)
#define cfu_op3_sw(rs1, rs2)  Cfu(3, rs1, rs2)

// useful name for each custom instruction
#define cfu_byte_sum_sw(rs1, rs2)    Cfu(0, rs1, rs2)
#define cfu_byte_swap_sw(rs1, rs2)   Cfu(1, rs1, rs2)
#define cfu_bit_reverse_sw(rs1, rs2) Cfu(2, rs1, rs2)
#define cfu_fib_sw(rs1, rs2) Cfu(3, rs1, rs2)



// =============== Switch HW vs SW

#ifdef CFU_FORCE_SW
#define cfu_op0(rs1, rs2)       cfu_op0_sw(rs1, rs2)
#define cfu_op1(rs1, rs2)       cfu_op1_sw(rs1, rs2)
#define cfu_op2(rs1, rs2)       cfu_op2_sw(rs1, rs2)
#define cfu_op3(rs1, rs2)       cfu_op3_sw(rs1, rs2)
#define cfu_byte_sum(rs1, rs2)    cfu_byte_sum_sw(rs1, rs2)
#define cfu_byte_swap(rs1, rs2)   cfu_byte_swap_sw(rs1, rs2)
#define cfu_bit_reverse(rs1, rs2) cfu_bit_reverse_sw(rs1, rs2)
#define cfu_fib(rs1, rs2) cfu_fib_sw(rs1, rs2)

#else

#define cfu_op0(rs1, rs2)       cfu_op0_hw((rs1), (rs2))
#define cfu_op1(rs1, rs2)       cfu_op1_hw((rs1), (rs2))
#define cfu_op2(rs1, rs2)       cfu_op2_hw((rs1), (rs2))
#define cfu_op3(rs1, rs2)       cfu_op3_hw((rs1), (rs2))
#define cfu_byte_sum(rs1, rs2)    cfu_byte_sum_hw((rs1), (rs2))
#define cfu_byte_swap(rs1, rs2)   cfu_byte_swap_hw((rs1), (rs2))
#define cfu_bit_reverse(rs1, rs2) cfu_bit_reverse_hw((rs1), (rs2))
#define cfu_fib(rs1, rs2) cfu_fib_hw((rs1), (rs2))

#endif
