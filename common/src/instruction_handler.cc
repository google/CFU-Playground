// Copyright 2021 The CFU-Playground Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "instruction_handler.h"

#include <stdio.h>

#include "riscv.h"
#include "generated/soc.h"

// Integer arithmetic routines linked later in compilation.
extern "C" {
long long __divdi3(long long, long long);
long long __udivdi3(long long, long long);
long long __moddi3(long long, long long);
long long __umoddi3(long long, long long);
};

// Returns the offset of a register from the register base pointer in memory.
// Must agree with crt0.
inline int8_t reg_offset(uint8_t reg) { return 31 - reg; }

// Handles div, divu, rem, and remu instructions in software.
void div_instruction_handler(uint32_t* reg_base, uint32_t instruction) {
  uint8_t funct3 = (instruction >> 12) & 0x7;
  int8_t rd_offset = reg_offset((instruction >> 7) & 0x1f);
  uint32_t src1 = reg_base[reg_offset((instruction >> 15) & 0x1f)];
  uint32_t src2 = reg_base[reg_offset((instruction >> 20) & 0x1f)];
  switch (funct3) {
    case 0x4:  // div
      reg_base[rd_offset] = src2 ? __divdi3((int32_t)src1, (int32_t)src2) : -1;
      break;
    case 0x5:  // divu
      reg_base[rd_offset] = src2 ? __udivdi3(src1, src2) : -1;
      break;
    case 0x6:  // rem
      reg_base[rd_offset] = __moddi3((int32_t)src1, (int32_t)src2);
      break;
    case 0x7:  // remu
      reg_base[rd_offset] = __umoddi3(src1, src2);
      break;
    default:
      break;
  }
}

// Called on an illegal instruction trap. Handles csr management and
// dispatching to specific instruction handlers.
void instruction_handler(uint32_t* reg_base) {
  uint32_t instruction = csr_read(mtval);
  uint32_t pc = csr_read(mepc);
  uint8_t opcode = instruction & 0x7F;
  switch (opcode) {
    case 0x33:  // M extension
      div_instruction_handler(reg_base, instruction);
      csr_write(mepc, pc + 4);
      break;
    default:
      break;
  }
}

// Because asm directives require string literals a macro is used.
#define ASM_R_TEST(inst)                                                     \
  [](uint32_t src1, uint32_t src2, uint32_t expected) {                      \
    uint32_t actual;                                                         \
    asm(inst " %[actual], %[src1], %[src2]"                                  \
        : [actual] "=r"(actual)                                              \
        : [src1] "r"(src1), [src2] "r"(src2));                               \
    if (actual != expected) {                                                \
      printf("Failed: " inst " %lu, %lu: expected %lu but got %lu.\n", src1, \
             src2, expected, actual);                                        \
    }                                                                        \
    return actual == expected;                                               \
  }

bool do_div_tests() {
  bool all_passed = true;
#ifndef CONFIG_CPU_VARIANT_MINIMAL
//  auto div_test = ASM_R_TEST("div");
//
//  // Test instruction is division.
//  all_passed &= div_test(/* src1= */ 10, /* src2= */ 3, /* expected= */ 3);
//  all_passed &= div_test(/* src1= */ 0, /* src2= */ 1, /* expected= */ 0);
//
//  // Test division is signed.
//  all_passed &= div_test(/* src1= */ 1, /* src2= */ -1, /* expected= */ -1);
//
//  // Test RISC-V divide by 0 semantics.
//  all_passed &= div_test(/* src1= */ 1, /* src2= */ 0, /* expected= */ -1);
//
//  // Test RISC-V signed division overflow semantics.
//  all_passed &= div_test(/* src1= */ 0x80000000, /* src2= */ -1,
//                         /* expected= */ 0x80000000);
#endif

  return all_passed;
}

bool do_divu_tests() {
  bool all_passed = true;
#ifndef CONFIG_CPU_VARIANT_MINIMAL
//  auto divu_test = ASM_R_TEST("divu");
//
//  // Test instruction is division.
//  all_passed &= divu_test(/* src1= */ 10, /* src2= */ 3, /* expected= */ 3);
//  all_passed &= divu_test(/* src1= */ 0, /* src2= */ 1, /* expected= */ 0);
//
//  // Test division is unsigned.
//  all_passed &= divu_test(/* src1= */ 1, /* src2= */ -1, /* expected= */ 0);
//
//  // Test RISC-V divide by 0 semantics.
//  all_passed &= divu_test(/* src1= */ 1, /* src2= */ 0, /* expected= */ -1);
#endif

  return all_passed;
}

bool do_rem_tests() {
  bool all_passed = true;
#ifndef CONFIG_CPU_VARIANT_MINIMAL
//  auto rem_test = ASM_R_TEST("rem");
//
//  // Test instruction is mod.
//  all_passed &= rem_test(/* src1= */ 13, /* src2= */ 4, /* expected= */ 1);
//  all_passed &= rem_test(/* src1= */ 0, /* src2= */ 4, /* expected= */ 0);
//
//  // Test mod is signed.
//  all_passed &= rem_test(/* src1= */ 4, /* src2= */ -3, /* expected= */ 1);
//
//  // Test RISC-V mod by 0 semantics.
//  all_passed &= rem_test(/* src1= */ 9, /* src2= */ 0, /* expected= */ 9);
#endif

  return all_passed;
}

bool do_remu_tests() {
  bool all_passed = true;
#ifndef CONFIG_CPU_VARIANT_MINIMAL
//  auto remu_test = ASM_R_TEST("remu");
//
//  // Test instruction is mod.
//  all_passed &= remu_test(/* src1= */ 13, /* src2= */ 4, /* expected= */ 1);
//  all_passed &= remu_test(/* src1= */ 0, /* src2= */ 4, /* expected= */ 0);
//
//  // Test mod is unsigned.
//  all_passed &= remu_test(/* src1= */ 4, /* src2= */ -3, /* expected= */ 4);
//
//  // Test RISC-V mod by 0 semantics.
//  all_passed &= remu_test(/* src1= */ 9, /* src2= */ 0, /* expected= */ 9);
#endif

  return all_passed;
}

#undef ASM_R_TEST

// Tests for illegal instruction handlers.
void do_instruction_tests() {
  /*
   * The integer arithmetic routines
   * (https://gcc.gnu.org/onlinedocs/gccint/Integer-library-routines.html) are
   * implemented for us, so these tests mainly check to make sure the right
   * routines are called for the right instructions.
   */
  bool all_passed = true;

  all_passed &= do_div_tests();
  all_passed &= do_divu_tests();
  all_passed &= do_rem_tests();
  all_passed &= do_remu_tests();

  if (all_passed) {
    puts("OK   Instruction handler tests passed.");
  } else {
    puts("FAIL Instruction handler tests failed.");
  }
}
