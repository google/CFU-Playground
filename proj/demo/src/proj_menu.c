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
#include "cfu.h"
#include "menu.h"
#include "proj_menu.h"

// Template Fn
static void do_hello_world(void)
{
    puts("Hello, World!!!\n");
}

// Test template instruction
static void do_grid_cfu_op0(void)
{
    puts("\nExercise CFU Op0\n");
    printf("a   b-->");
    for (int b = 0; b < 6; b++)
    {
        printf("%8d", b);
    }
    puts("\n-------------------------------------------------------");
    for (int a = 0; a < 6; a++)
    {
        printf("%-8d", a);
        for (int b = 0; b < 6; b++)
        {
            int cfu = cfu_op0(0, a, b);
            printf("%8d", cfu);
        }
        puts("");
    }
}

// Test template instruction
static void do_grid_cfu_op1(void)
{
    puts("\nExercise CFU Op1\n");
    printf("a   b-->");
    for (int b = 0; b < 6; b++)
    {
        printf("%8d", b);
    }
    puts("\n-------------------------------------------------------");
    for (int a = 0; a < 6; a++)
    {
        printf("%-8d", a);
        for (int b = 0; b < 6; b++)
        {
            int cfu = cfu_op1(0, a, b);
            printf("%8d", cfu);
        }
        puts("");
    }
}


// Test cfu instruction against sw
static void do_exercise_cfu_op0(void)
{
    puts("\nExercise CFU Op0...\n");
    int count = 0;
    for (unsigned a = 0x00000067u; a < 0xf8000000u; a += 0x00112345u)
    {
        for (unsigned b = 0x00000a98u; b < 0xf8000000u; b += 0x00270077u)
        {
            int cfu    = cfu_op0(0, a, b);
            int cfu_sw = cfu_op0_sw(0, a, b);
            //printf("a: %08x b:%08x cfu=%08x  expect=%08x\n", a, b, cfu, cfu_sw);
            if (cfu != cfu_sw) 
            {
                printf("\n***FAIL\n");
                return;
            }
            count++;
        }
    }
    printf("PASS  Performed %d comparisons\n\n", count);
}

// Test cfu instruction against sw
static void do_exercise_cfu_op1(void)
{
    puts("\nExercise CFU Op1...\n");
    int count = 0;
    for (unsigned a = 0x00000067u; a < 0xf8000000u; a += 0x00112345u)
    {
        for (unsigned b = 0x00000a98u; b < 0xf8000000u; b += 0x00270077u)
        {
            int cfu    = cfu_op1(0, a, b);
            int cfu_sw = cfu_op1_sw(0, a, b);
            //printf("a: %08x b:%08x cfu=%08x  expect=%08x\n", a, b, cfu, cfu_sw);
            if (cfu != cfu_sw) 
            {
                printf("a: %08x b:%08x cfu=%08x  expect=%08x\n", a, b, cfu, cfu_sw);
                printf("\n***FAIL\n");
                return;
            }
            count++;
        }
    }
    printf("PASS  Performed %d comparisons\n\n", count);
}


static struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('0', "check cfu op0 against sw", do_exercise_cfu_op0),
        MENU_ITEM('1', "check cfu op1 against sw", do_exercise_cfu_op1),
        MENU_ITEM('g', "grid cfu op0", do_grid_cfu_op0),
        MENU_ITEM('j', "grid cfu op1", do_grid_cfu_op1),
        MENU_ITEM('h', "say Hello", do_hello_world),
        MENU_END,
    },
};

void do_proj_menu()
{
    menu_run(&MENU);
}
