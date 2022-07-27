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

#include "third_party/embench_iot_v1/embench.h"
#include "third_party/embench_iot_v1/src/embench_wrapper.h"
#include "menu.h"

#include <stdio.h>

inline void no_menu() {}

// Automatically incrementing compile time constant character.
// Used for avoiding selection character collisions in the menu.
#define STARTING_SEL_CHAR 0x31  // '1'
#define AUTO_INC_CHAR __COUNTER__ + STARTING_SEL_CHAR

static struct Menu MENU = {
    "Embench IoT",
    "benchmarks",
    {
#if defined(INCLUDE_EMBENCH_PRIMECOUNT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "Primecount", embench_wrapper_primecount),
#endif
#if defined(INCLUDE_EMBENCH_MINVER) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "Minver", embench_wrapper_minver),
#endif
#if AUTO_INC_CHAR == STARTING_SEL_CHAR
        MENU_ITEM('!', "No Embench workloads selected! Check defines in Makefile!",
                  no_menu),
#endif
        MENU_END,
    },
};

#undef AUTO_INC_CHAR
#undef STARTING_SEL_CHAR

// For integration into menu system
void embench_menu() { menu_run(&MENU); }
