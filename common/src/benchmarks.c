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
#include "menu.h"
#include "perf.h"
#include "benchmarks.h"


extern int buf[128*1024];

int buf[128*1024];
int * volatile p;


// Each project should make their own proj_menu.c, which will replace this one.

static void __attribute__ ((noinline)) do_loads_cached(void) {
    puts("Hello, Load!\n");
    int acc=0;
    for (int j=0; j<1024; ++j) {        // warmup
        acc += buf[j];
    }
    int start_time = perf_get_mcycle();
    for (int i=0; i<1024; ++i) {
        for (int j=0; j<1024; ++j) {
            acc += buf[j];
        }
        *p = acc;
    }
    int end_time = perf_get_mcycle();
    printf("Val:%d  Cycles: %d   Cycles/load: %d\n\n\n",
        acc, end_time-start_time, (end_time-start_time) / (16*64*1024));
}

static void __attribute__ ((noinline)) do_loads(void) {
    puts("Hello, Load!\n");
    int acc=0;
    int start_time = perf_get_mcycle();
    for (int i=0; i<8; ++i) {
        for (int j=0; j<128*1024; ++j) {
            acc += buf[j];
        }
        *p = acc;
    }
    int end_time = perf_get_mcycle();
    printf("Val:%d  Cycles: %d   Cycles/load: %d\n\n\n",
        acc, end_time-start_time, (end_time-start_time) / (16*64*1024));
}

static void __attribute__ ((noinline)) do_stores(void) {
    puts("Hello, Store!\n");
    int acc=0;
    int start_time = perf_get_mcycle();
    for (int i=0; i<8; ++i) {
        for (int j=0; j<128*1024; ++j) {
            buf[j] = i;
        }
        acc += *p;
    }
    int end_time = perf_get_mcycle();
    printf("Val:%d  Cycles: %d   Cycles/store: %d\n\n\n",
        acc, end_time-start_time, (end_time-start_time) / (16*64*1024));
}

static void __attribute__ ((noinline)) do_increment_mem(void) {
    puts("Hello, Increment!\n");
    int acc=0;
    int start_time = perf_get_mcycle();
    for (int i=0; i<8; ++i) {
        for (int j=0; j<128*1024; ++j) {
            buf[j] += i;
        }
        acc += *p;
    }
    int end_time = perf_get_mcycle();
    printf("Val:%d  Cycles: %d   Cycles/(load-add-store): %d\n\n\n",
        acc, end_time-start_time, (end_time-start_time) / (16*64*1024));
}

static struct Menu MENU = {
    "Benchmarks Menu",
    "benchmark",
    {
        MENU_ITEM('l', "sequential loads benchmark (expect one miss per cache line)", do_loads),
        MENU_ITEM('c', "cached loads benchmark (expect all hits)", do_loads_cached),
        MENU_ITEM('s', "sequential stores benchmark", do_stores),
        MENU_ITEM('i', "load-increment-store benchmark (expect misses)", do_increment_mem),
        MENU_END,
    },
};

void do_benchmarks_menu()
{
  p = buf + 3;
  menu_run(&MENU);
}
