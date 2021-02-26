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

#include <stdio.h>

#include "riscv.h"
#include "cfu.h"

#include "base.h"
#include "functional_cfu_tests.h"
#include "menu.h"

#include "generated/csr.h"

static void do_fixed_tests(void)
{
    puts("CFU TEST for op0, 1 and 2:");
    puts("arg0        arg1        op0         op1         op2");
    for (uint32_t i = 0; i < 0x50505; i += 0x8103)
    {
        uint32_t j = i ^ 0xffff;
        uint32_t v0 = cfu_op0(i, j);
        uint32_t v1 = cfu_op1(i, j);
        uint32_t v2 = cfu_op2(i, j);
        printf("0x%08x, 0x%08x: 0x%08x, 0x%08x, 0x%08x\n", i, j, v0, v1, v2);
    }
}

static void do_compare_tests(void)
{
    puts("CFU COMPARE TEST for op0, 1, and 2:");
    int count = 0;
    for (uint32_t i = 0; i < 0x5050505; i += 0x7105)
    {
        for (uint32_t j = 0; j < 0x5050505; j += 0xb103)
        {
            uint32_t hw0 = cfu_op0_hw(i, j);
            uint32_t hw1 = cfu_op1_hw(i, j);
            uint32_t hw2 = cfu_op2_hw(i, j);
            uint32_t sw0 = cfu_op0_sw(i, j);
            uint32_t sw1 = cfu_op1_sw(i, j);
            uint32_t sw2 = cfu_op2_sw(i, j);
            if (hw0 != sw0 || hw1 != sw1 || hw2 != sw2)
            {
                puts("arg0        arg1            fn0               fn1              fn2");
                printf("0x%08x, 0x%08x: 0x%08x:0x%08x, 0x%08x:0x%08x, 0x%08x:0x%08x <<=== MISMATCH!\n",
                       i, j, hw0, sw0, hw1, sw1, hw2, sw2);
            }
            ++count;
            if ((count & 0xffff) == 0)
                printf("Ran %d comparisons....\n", count);
        }
    }
    printf("Ran %d comparisons.\n", count);
}

static void print_result(int op, uint32_t v0, uint32_t v1, uint32_t r) {
    printf("cfu_op%1d(%08x, %08x) = %08x (hex), %d (signed), %u (unsigned)\n", op, v0, v1, r, r, r);

}

static void do_interactive_tests(void)
{
    puts("CFU Interactive Test:");

    uint32_t v0 = read_val("  First operand value  ");
    uint32_t v1 = read_val("  Second operand value ");
    print_result(0, v0, v1, cfu_op0(v0, v1));
    print_result(1, v0, v1, cfu_op1(v0, v1));
    print_result(2, v0, v1, cfu_op2(v0, v1));
    print_result(3, v0, v1, cfu_op3(v0, v1));
    print_result(4, v0, v1, cfu_op4(v0, v1));
    print_result(5, v0, v1, cfu_op5(v0, v1));
    print_result(6, v0, v1, cfu_op6(v0, v1));
    print_result(7, v0, v1, cfu_op7(v0, v1));
}

static struct Menu MENU = {
    "Tests for Functional CFUs",
    "functional",
    {
        MENU_ITEM('f', "Run fixed CFU tests", do_fixed_tests),
        MENU_ITEM('c', "Run hw/sw compare tests", do_compare_tests),
        MENU_ITEM('i', "Run interactive tests", do_interactive_tests),
        MENU_END,
    },
};

void do_functional_cfu_tests()
{
    sim_trace_enable_write(true);
    menu_run(&MENU);
}
