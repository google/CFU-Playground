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
#include <stdio.h>

#include "tflite.h"
#include "menu.h"
#include "functional_cfu_tests.h"
#include "models/pdti8/pdti8.h"
#include "proj_menu.h"
#include "perf.h"
#include "base.h"


static struct Menu MENU = {
    "CFU Playground",
    "main",
    {
        MENU_ITEM('1', "pdti8 model", pdti8_menu),
        MENU_ITEM('2', "Functional CFU Tests", do_functional_cfu_tests),
        MENU_ITEM('3', "Project menu", do_proj_menu),
        MENU_ITEM('4', "Performance Counter Tests", perf_test_menu),
        MENU_ITEM('5', "TFLite Unit Tests", tflite_do_tests),
        MENU_SENTINEL,
    },
};

int main(void)
{
  init_runtime();
  printf("Hello, %s!\n", "World");

  puts("initTfLite()");

  menu_run(&MENU);

  return (0);
}
