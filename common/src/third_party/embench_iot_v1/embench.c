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
        MENU_ITEM(AUTO_INC_CHAR, "primecount", embench_wrapper_primecount),
#endif
#if defined(INCLUDE_EMBENCH_MINVER) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "minver", embench_wrapper_minver),
#endif
#if defined(INCLUDE_EMBENCH_AHA_MONT64) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "aha-mont64", embench_wrapper_aha_mont64),
#endif
#if defined(INCLUDE_EMBENCH_CRC_32) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "crc_32", embench_wrapper_crc_32),
#endif
#if defined(INCLUDE_EMBENCH_CUBIC) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "cubic", embench_wrapper_cubic),
#endif
#if defined(INCLUDE_EMBENCH_EDN) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "edn", embench_wrapper_edn),
#endif
#if defined(INCLUDE_EMBENCH_HUFFBENCH) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "huffbench", embench_wrapper_huffbench),
#endif
#if defined(INCLUDE_EMBENCH_MATMUL) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "matmul", embench_wrapper_matmul),
#endif
#if defined(INCLUDE_EMBENCH_MD5) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "md5sum", embench_wrapper_md5),
#endif
#if defined(INCLUDE_EMBENCH_NBODY) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "nbody", embench_wrapper_nbody),
#endif
#if defined(INCLUDE_EMBENCH_NETTLE_AES) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "nettle-aes", embench_wrapper_nettle_aes),
#endif
#if defined(INCLUDE_EMBENCH_NETTLE_SHA256) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "nettle-sha256", embench_wrapper_nettle_sha256),
#endif
#if defined(INCLUDE_EMBENCH_NSICHNEU) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "nsichneu", embench_wrapper_nsichneu),
#endif
#if defined(INCLUDE_EMBENCH_QRDUINO) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "qrduino", embench_wrapper_qrduino),
#endif
#if defined(INCLUDE_EMBENCH_SLRE) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "slre", embench_wrapper_slre),
#endif
#if defined(INCLUDE_EMBENCH_ST) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "st", embench_wrapper_st),
#endif
#if defined(INCLUDE_EMBENCH_STATEMATE) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "statemate", embench_wrapper_statemate),
#endif
#if defined(INCLUDE_EMBENCH_TARFIND) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "tarfind", embench_wrapper_tarfind),
#endif
#if defined(INCLUDE_EMBENCH_UD) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "ud", embench_wrapper_ud),
#endif
#if defined(INCLUDE_EMBENCH_WIKISORT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
        MENU_ITEM(AUTO_INC_CHAR, "wikisort", embench_wrapper_wikisort),
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
