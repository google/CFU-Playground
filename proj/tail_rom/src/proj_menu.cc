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

#include "calc_once_data.h"
#include "menu.h"
#include "proj_menu.h"

#ifdef TAIL_ROM_USE
#include "pdti8_cache.h"
#endif

namespace {

void do_reset_cache() { calculate_once::SetCache(NULL); }

void do_set_pdti8() {
#ifdef TAIL_ROM_USE
  calculate_once::SetCache(GetCachePdti8());
#else
  puts("Not configured to use tail rom.");
#endif
}

struct Menu MENU = {
    "Project Menu",
    "project",
    {
        MENU_ITEM('0', "reset cache", do_reset_cache),
        MENU_ITEM('1', "Set cache for pdti8", do_set_pdti8),
        MENU_END,
    },
};

}  // anonymous namespace

extern "C" void do_proj_menu() { menu_run(&MENU); }
