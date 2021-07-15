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


// crt0 for VexRiscV running from program loaded into RAM
// if running from flash, will need to initialize data from flash

#include "generated/soc.h"

.global main
.global isr

.section .text.start
.global _start

_start:
  j crt_init
  nop
  nop
  nop
  nop
  nop
  nop
  nop

.section .text
.global  trap_entry
trap_entry:
#ifdef CONFIG_CPU_DIV_UNIMPLEMENTED
  // Need to save all registers for the illegal instruction handler.

  sw x1, -1 * 4(sp)
  // x2 is sp, skip word to make register retrieval easy.
  sw x3, -3 * 4(sp)
  sw x4, -4 * 4(sp)
  sw x5, -5 * 4(sp)
  sw x6, -6 * 4(sp)
  sw x7, -7 * 4(sp)
  sw x8, -8 * 4(sp)
  sw x9, -9 * 4(sp)
  sw x10, -10 * 4(sp)
  sw x11, -11 * 4(sp)
  sw x12, -12 * 4(sp)
  sw x13, -13 * 4(sp)
  sw x14, -14 * 4(sp)
  sw x15, -15 * 4(sp)
  sw x16, -16 * 4(sp)
  sw x17, -17 * 4(sp)
  sw x18, -18 * 4(sp)
  sw x19, -19 * 4(sp)
  sw x20, -20 * 4(sp)
  sw x21, -21 * 4(sp)
  sw x22, -22 * 4(sp)
  sw x23, -23 * 4(sp)
  sw x24, -24 * 4(sp)
  sw x25, -25 * 4(sp)
  sw x26, -26 * 4(sp)
  sw x27, -27 * 4(sp)
  sw x28, -28 * 4(sp)
  sw x29, -29 * 4(sp)
  sw x30, -30 * 4(sp)
  sw x31, -31 * 4(sp)
  addi sp, sp, -31 * 4

  mv a0, sp // Copy the sp as argument 0, used for retrieving stored regs.
  call trap_handler

  lw x1, 30 * 4(sp)
  // x2 is sp.
  lw x3, 28 * 4(sp)
  lw x4, 27 * 4(sp)
  lw x5, 26 * 4(sp)
  lw x6, 25 * 4(sp)
  lw x7, 24 * 4(sp)
  lw x8, 23 * 4(sp)
  lw x9, 22 * 4(sp)
  lw x10, 21 * 4(sp)
  lw x11, 20 * 4(sp)
  lw x12, 19 * 4(sp)
  lw x13, 18 * 4(sp)
  lw x14, 17 * 4(sp)
  lw x15, 16 * 4(sp)
  lw x16, 15 * 4(sp)
  lw x17, 14 * 4(sp)
  lw x18, 13 * 4(sp)
  lw x19, 12 * 4(sp)
  lw x20, 11 * 4(sp)
  lw x21, 10 * 4(sp)
  lw x22, 9 * 4(sp)
  lw x23, 8 * 4(sp)
  lw x24, 7 * 4(sp)
  lw x25, 6 * 4(sp)
  lw x26, 5 * 4(sp)
  lw x27, 4 * 4(sp)
  lw x28, 3 * 4(sp)
  lw x29, 2 * 4(sp)
  lw x30, 1 * 4(sp)
  lw x31, 0 * 4(sp)
  addi sp, sp, 31 * 4
#else
  sw x1,  - 1*4(sp)
  sw x5,  - 2*4(sp)
  sw x6,  - 3*4(sp)
  sw x7,  - 4*4(sp)
  sw x10, - 5*4(sp)
  sw x11, - 6*4(sp)
  sw x12, - 7*4(sp)
  sw x13, - 8*4(sp)
  sw x14, - 9*4(sp)
  sw x15, -10*4(sp)
  sw x16, -11*4(sp)
  sw x17, -12*4(sp)
  sw x28, -13*4(sp)
  sw x29, -14*4(sp)
  sw x30, -15*4(sp)
  sw x31, -16*4(sp)
  addi sp,sp,-16*4
  call isr
  lw x1 , 15*4(sp)
  lw x5,  14*4(sp)
  lw x6,  13*4(sp)
  lw x7,  12*4(sp)
  lw x10, 11*4(sp)
  lw x11, 10*4(sp)
  lw x12,  9*4(sp)
  lw x13,  8*4(sp)
  lw x14,  7*4(sp)
  lw x15,  6*4(sp)
  lw x16,  5*4(sp)
  lw x17,  4*4(sp)
  lw x28,  3*4(sp)
  lw x29,  2*4(sp)
  lw x30,  1*4(sp)
  lw x31,  0*4(sp)
  addi sp,sp,16*4
#endif // CONFIG_CPU_DIV_UNIMPLEMENTED
  mret
  .text


crt_init:
  la sp, _fstack + 4
  la a0, trap_entry
  csrw mtvec, a0

  // Move initialized data from ROM to RAM
  la t0, _erodata
  la t1, _fdata
  la t2, _edata
1:
  beq t1, t2, 2f
  lw t3, 0(t0)
  sw t3, 0(t1)
  addi t0, t0, 4
  addi t1, t1, 4
  j 1b
2:

  // Zero BSS RAM
  la a0, _fbss
  la a1, _ebss
3:
  beq a0,a1, 4f
  sw zero,0(a0)
  add a0,a0,4
  j 3b
4:

    //880 enable timer + external interrupt sources (until mstatus.MIE is set, they will never trigger an interrupt)
  li a0, 0x880 
  csrw mie,a0

  call main
infinit_loop:
  j infinit_loop
