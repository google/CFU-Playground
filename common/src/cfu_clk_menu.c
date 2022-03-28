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

#include "cfu_clk_menu.h"
#include "menu.h"

#include <generated/csr.h>

#include <stdio.h>

static void do_cfu_clk_enable () {
    puts("Enabling CFU clock\n");
    cfu_ctl_csr_write(1);
}

static void do_cfu_clk_disable () {
    puts("Disabling CFU clock\n");
    cfu_ctl_csr_write(0);
}

struct Menu MENU = {
    "CFU clock control menu",
    "cfu_clock",
    {
        MENU_ITEM('1', "Enable CFU clock", do_cfu_clk_enable),
        MENU_ITEM('0', "Disable CFU clock", do_cfu_clk_disable),
        MENU_END,
    },
};

void cfu_clk_menu() {
    menu_run(&MENU);
}
