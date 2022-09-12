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

#include <console.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/soc.h>
#include <stdio.h>

#include "base.h"
#include "benchmarks.h"
#include "donut.h"
#include "fb_util.h"
#include "functional_cfu_tests.h"
#include "instruction_handler.h"
#include "menu.h"
#include "perf.h"
#include "playground_util/util_tests.h"
#include "proj_menu.h"
#include "spiflash.h"
#include "tflite_unit_tests.h"
#include "third_party/embench_iot_v1/embench.h"
#ifndef SKIP_TFLM
#include "models/models.h"
#endif

#ifdef PLATFORM_sim
static void trace_sim() {
  puts("Beginning trace");
  sim_trace_enable_write(1);
}
static void exit_sim() {
  puts("Goodbye!");
  sim_finish_finish_write(1);
}
#endif

static struct Menu MENU = {
    "CFU Playground",
    "main",
    {
#ifndef SKIP_TFLM
        MENU_ITEM('1', "TfLM Models menu", models_menu),
#endif
        MENU_ITEM('2', "Functional CFU Tests", do_functional_cfu_tests),
        MENU_ITEM('3', "Project menu", do_proj_menu),
        MENU_ITEM('4', "Performance Counter Tests", perf_test_menu),
#ifndef SKIP_TFLM
        MENU_ITEM('5', "TFLite Unit Tests", tflite_do_tests),
#endif
        MENU_ITEM('6', "Benchmarks", do_benchmarks_menu),
        MENU_ITEM('7', "Util Tests", do_util_tests_menu),
        MENU_ITEM('8', "Embench IoT", embench_menu),
#ifdef DONUT_DEMO
        MENU_ITEM('d', "Donut demo", donut),
#endif
#ifdef SPIFLASH_BASE
        MENU_ITEM('9', "SPI Flash Debugging", spiflash_menu),
#endif
#ifdef CONFIG_CPU_DIV_UNIMPLEMENTED
        MENU_ITEM('I', "Illegal Instruction Tests (these *WILL* hang on Fomu!)",
                  do_instruction_tests),
#endif
#ifdef CSR_VIDEO_FRAMEBUFFER_BASE
        MENU_ITEM('10', "Framebuffer Debugging", framebuffer_menu),
#endif
#ifdef PLATFORM_sim
        MENU_ITEM('t', "trace (only works in simulation)", trace_sim),
        MENU_ITEM('Q', "Exit (only works in simulation)", exit_sim),
#endif
        MENU_SENTINEL,
    },
};

int main(void) {
  init_runtime();
  printf("Hello, %s!\n", "World");

  menu_run(&MENU);

  return (0);
}
