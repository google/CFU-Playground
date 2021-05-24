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

#include "benchmarks.h"

#include <stdio.h>

#include "assert.h"
#include "menu.h"
#include "perf.h"
#include "generated/mem.h"

#ifdef PLATFORM_hps
#define BUF_SIZE (32 * 1024)  // must be at least 1024
#else
#define BUF_SIZE (128 * 1024)  // must be at least 1024
#endif

// Each project should make their own proj_menu.c, which will replace this one.

static void __attribute__((noinline)) do_loads_cached(void) {
  puts("Hello, Cached Load!\n");
  assert(BUF_SIZE >= 1024);
  int buf[BUF_SIZE];
  int acc = 0;
  for (int j = 0; j < 1024; ++j) {  // warmup
    acc += buf[j];
  }
  int start_time = perf_get_mcycle();
  for (int i = 0; i < 1024; ++i) {
    for (int j = 0; j < 1024; ++j) {
      acc += buf[j];
    }
    buf[i] = acc;  // inhibit optimization
  }
  int end_time = perf_get_mcycle();
  int total_iters = 1024 * 1024;
  printf("Val:%d  Cycles: %d   Cycles/load: %d\n\n\n", acc,
         end_time - start_time, (end_time - start_time) / total_iters);
}

static void __attribute__((noinline)) do_loads_strided(void) {
  puts("Hello, Strided Load!\n");
  int buf[BUF_SIZE];
  int acc = 0;
  int start_time = perf_get_mcycle();
  for (int i = 0; i < 64; ++i) {
    // 32 bytes per cache line, so stride by 8 4-byte ints
    for (int j = 0; j < BUF_SIZE; j += 8) {
      acc += buf[j];
    }
    buf[i] = acc;  // inhibit optimization
  }
  int end_time = perf_get_mcycle();
  int total_iters = 64 * BUF_SIZE / 8;
  printf("Val:%d  Cycles: %d   Cycles/load: %d\n\n\n", acc,
         end_time - start_time, (end_time - start_time) / total_iters);
}

#ifdef SPIFLASH_BASE

static void __attribute__((noinline)) do_flash_loads(void) {
  printf("Hello, Flash Load! (SPI flash at %p, size %dkB)\n", SPIFLASH_BASE, (SPIFLASH_SIZE/1024));
  int*  buf = (int*)((void*)(SPIFLASH_BASE));
  int acc = 0;
  unsigned int start_time = perf_get_mcycle();
  int total_iters = 64*1024;
  for (int j = 0; j<total_iters; j++) {
    acc += buf[j];
  }
  unsigned int end_time = perf_get_mcycle();
  unsigned int delta_cycles = end_time - start_time;
  printf("Val:%d  Cycles: %u   Cycles/load: %u\n\n\n", acc,
         delta_cycles, delta_cycles / total_iters);
}

static void __attribute__((noinline)) do_flash_loads_strided_2x(void) {
  printf("Hello, STRIDED Flash Load! (SPI flash at %p, size %dkB)\n", SPIFLASH_BASE, (SPIFLASH_SIZE/1024));
  int*  buf = (int*)((void*)(SPIFLASH_BASE));
  int acc = 0;
  unsigned int start_time = perf_get_mcycle();
  int total_iters = 64*1024;
  for (int j = 0; j<total_iters; j++) {
    acc += buf[j*2];    // 2x stride
  }
  unsigned int end_time = perf_get_mcycle();
  unsigned int delta_cycles = end_time - start_time;
  printf("Val:%d  Cycles: %u   Cycles/load: %u\n\n\n", acc,
         delta_cycles, delta_cycles / total_iters);
}

static void __attribute__((noinline)) do_flash_loads_strided_4x(void) {
  printf("Hello, STRIDED Flash Load! (SPI flash at %p, size %dkB)\n", SPIFLASH_BASE, (SPIFLASH_SIZE/1024));
  int*  buf = (int*)((void*)(SPIFLASH_BASE));
  int acc = 0;
  unsigned int start_time = perf_get_mcycle();
  int total_iters = 64*1024;
  for (int j = 0; j<total_iters; j++) {
    acc += buf[j*4];    // 4x stride
  }
  unsigned int end_time = perf_get_mcycle();
  unsigned int delta_cycles = end_time - start_time;
  printf("Val:%d  Cycles: %u   Cycles/load: %u\n\n\n", acc,
         delta_cycles, delta_cycles / total_iters);
}

static void __attribute__((noinline)) do_flash_loads_strided_8x(void) {
  printf("Hello, STRIDED Flash Load! (SPI flash at %p, size %dkB)\n", SPIFLASH_BASE, (SPIFLASH_SIZE/1024));
  int*  buf = (int*)((void*)(SPIFLASH_BASE));
  int acc = 0;
  unsigned int start_time = perf_get_mcycle();
  int total_iters = 32*1024;
  for (int j = 0; j<total_iters; j++) {
    acc += buf[j*8];    // 8x stride
  }
  unsigned int end_time = perf_get_mcycle();
  unsigned int delta_cycles = end_time - start_time;
  printf("Val:%d  Cycles: %u   Cycles/load: %u\n\n\n", acc,
         delta_cycles, delta_cycles / total_iters);
}

static void __attribute__((noinline)) do_flash_loads_strided_16x(void) {
  printf("Hello, STRIDED Flash Load! (SPI flash at %p, size %dkB)\n", SPIFLASH_BASE, (SPIFLASH_SIZE/1024));
  int*  buf = (int*)((void*)(SPIFLASH_BASE));
  int acc = 0;
  unsigned int start_time = perf_get_mcycle();
  int total_iters = 16*1024;
  for (int j = 0; j<total_iters; j++) {
    acc += buf[j*16];    // 16x stride
  }
  unsigned int end_time = perf_get_mcycle();
  unsigned int delta_cycles = end_time - start_time;
  printf("Val:%d  Cycles: %u   Cycles/load: %u\n\n\n", acc,
         delta_cycles, delta_cycles / total_iters);
}

static void __attribute__((noinline)) do_flash_loads_strided_32x(void) {
  printf("Hello, STRIDED Flash Load! (SPI flash at %p, size %dkB)\n", SPIFLASH_BASE, (SPIFLASH_SIZE/1024));
  int*  buf = (int*)((void*)(SPIFLASH_BASE));
  int acc = 0;
  unsigned int start_time = perf_get_mcycle();
  int total_iters = 16*1024;
  for (int j = 0; j<total_iters; j++) {
    acc += buf[j*32];    // 32x stride
  }
  unsigned int end_time = perf_get_mcycle();
  unsigned int delta_cycles = end_time - start_time;
  printf("Val:%d  Cycles: %u   Cycles/load: %u\n\n\n", acc,
         delta_cycles, delta_cycles / total_iters);
}

#endif

static void __attribute__((noinline)) do_loads(void) {
  puts("Hello, Load!\n");
  int buf[BUF_SIZE];
  int acc = 0;
  int start_time = perf_get_mcycle();
  for (int i = 0; i < 8; ++i) {
    for (int j = 0; j < BUF_SIZE; ++j) {
      acc += buf[j];
    }
    buf[i] = acc;  // inhibit optimization
  }
  int end_time = perf_get_mcycle();
  int total_iters = 8 * BUF_SIZE;
  printf("Val:%d  Cycles: %d   Cycles/load: %d\n\n\n", acc,
         end_time - start_time, (end_time - start_time) / total_iters);
}

static void __attribute__((noinline)) do_stores(void) {
  puts("Hello, Store!\n");
  int buf[BUF_SIZE];
  int acc = 0;
  int start_time = perf_get_mcycle();
  for (int i = 0; i < 8; ++i) {
    for (int j = 0; j < BUF_SIZE; ++j) {
      buf[j] = i;
    }
    acc += buf[i];  // inhibit optimization
  }
  int end_time = perf_get_mcycle();
  int total_iters = 8 * BUF_SIZE;
  printf("Val:%d  Cycles: %d   Cycles/store: %d\n\n\n", acc,
         end_time - start_time, (end_time - start_time) / (total_iters));
}

static void __attribute__((noinline)) do_increment_mem(void) {
  puts("Hello, Increment!\n");
  int buf[BUF_SIZE];
  int acc = 0;
  int start_time = perf_get_mcycle();
  for (int i = 0; i < 8; ++i) {
    for (int j = 0; j < BUF_SIZE; ++j) {
      buf[j] += i;
    }
    acc += buf[i];  // inhibit optimization
  }
  int end_time = perf_get_mcycle();
  int total_iters = 8 * BUF_SIZE;
  printf("Val:%d  Cycles: %d   Cycles/(load-add-store): %d\n\n\n", acc,
         end_time - start_time, (end_time - start_time) / total_iters);
}

static struct Menu MENU = {
    "Benchmarks Menu",
    "benchmark",
    {
        MENU_ITEM('l',
                  "sequential loads benchmark (expect one miss per cache line, "
                  "one every eight accesses)",
                  do_loads),
#ifdef SPIFLASH_BASE
        MENU_ITEM('f', "flash sequential loads benchmark", do_flash_loads),
        MENU_ITEM('g', "flash STRIDED 2x loads benchmark", do_flash_loads_strided_2x),
        MENU_ITEM('4', "flash STRIDED 4x loads benchmark", do_flash_loads_strided_4x),
        MENU_ITEM('8', "flash STRIDED 8x loads benchmark", do_flash_loads_strided_8x),
        MENU_ITEM('y', "flash STRIDED 16x loads benchmark", do_flash_loads_strided_16x),
        MENU_ITEM('z', "flash STRIDED 32x loads benchmark", do_flash_loads_strided_32x),
#endif
        MENU_ITEM('c', "cached loads benchmark (expect all hits)",
                  do_loads_cached),
        MENU_ITEM('e', "strided loads benchmark (expect all misses)",
                  do_loads_strided),
        MENU_ITEM('s', "sequential stores benchmark", do_stores),
        MENU_ITEM('i', "load-increment-store benchmark (expect misses)",
                  do_increment_mem),
        MENU_END,
    },
};

void do_benchmarks_menu() { menu_run(&MENU); }
