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

#include "proj_menu.h"

#include <stdio.h>

#include "blocks_test.h"
#include "cfu.h"
#include "menu.h"

static struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('m', "test blocks Multiply", do_test_blocks_multiply_accumulate),
        MENU_ITEM('f', "test blocks Filter", do_test_blocks_filter),
        MENU_ITEM('i', "test blocks Input", do_test_blocks_input),
        MENU_END,
    },
};

void do_proj_menu() { menu_run(&MENU); }
