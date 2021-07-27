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

#include "menu.h"

// Each project should make their own proj_menu.c, which will replace this one.
namespace {
void do_hello_world(void) { puts("Hello, World!\n"); }

struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('h', "say Hello", do_hello_world),
        MENU_END,
    },
};
};  // namespace

extern "C" void do_proj_menu() { menu_run(&MENU); }