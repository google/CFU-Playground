
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


// generic name for each custom instruction
#define cfu_op0(rs1, rs2)  opcode_R(CUSTOM0, 0, 0, (rs1), (rs2))
#define cfu_op1(rs1, rs2)  opcode_R(CUSTOM0, 1, 0, (rs1), (rs2))
#define cfu_op2(rs1, rs2)  opcode_R(CUSTOM0, 2, 0, (rs1), (rs2))

// useful name for each custom instruction
#define cfu_byte_sum(rs1, rs2)  opcode_R(CUSTOM0, 0, 0, (rs1), (rs2))
#define cfu_byte_swap(rs1, rs2)  opcode_R(CUSTOM0, 1, 0, (rs1), (rs2))
#define cfu_bit_reverse(rs1, rs2)  opcode_R(CUSTOM0, 2, 0, (rs1), (rs2))

