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
#include "models/pdti8/pdti8.h"
#include "tflite.h"
#include "menu.h"

#include "models/pdti8/model_pdti8.h"

#include "tensorflow/lite/micro/examples/person_detection_experimental/person_image_data.h"
#include "tensorflow/lite/micro/examples/person_detection_experimental/no_person_image_data.h"

static const int kPersonIndex = 1;
static const int kNotAPersonIndex = 0;

// Initialize everything once
// deallocate tensors when done
static void pdti8_init(void)
{
    tflite_load_model(model_pdti8);
}

// Run classification, after input has been loaded
static void pdti8_classify(int8_t *results)
{
    printf("Running pdti8\n");
    tflite_classify();

    // Process the inference results.
    int8_t *output = tflite_get_output();
    printf("Person:     %4d\n", output[kPersonIndex]);
    printf("Not person: %4d\n", output[kNotAPersonIndex]);
    if (results)
    {
        results[0] = output[0];
        results[1] = output[1];
    }
}

static void do_classify_zeros()
{
    tflite_set_input_zeros();
    pdti8_classify(NULL);
}

static void do_classify_no_person()
{
    puts("Classify Not Person");
    tflite_set_input(g_no_person_data);
    pdti8_classify(NULL);
}

static void do_classify_person()
{
    puts("Classify Person");
    tflite_set_input(g_person_data);
    pdti8_classify(NULL);
}

#define NUM_GOLDEN 3
static int8_t golden_results[NUM_GOLDEN][2] = {
    {72, -72},
    {-25, 25},
    {-113, 113},
};

static void do_golden_tests()
{
    int8_t actual[NUM_GOLDEN][2];
    tflite_set_input_zeros();
    pdti8_classify(actual[0]);
    tflite_set_input(g_no_person_data);
    pdti8_classify(actual[1]);
    tflite_set_input(g_person_data);
    pdti8_classify(actual[2]);

    bool failed = false;
    for (size_t i = 0; i < NUM_GOLDEN; i++)
    {
        if (actual[i][0] != golden_results[i][0] || actual[i][1] != golden_results[i][1])
        {
            failed = true;
            printf("*** Golden test %d failed (%d, %d)\n", i, actual[i][0], actual[i][1]);
        }
    }

    if (failed)
    {
        puts("FAIL Golden tests failed");
    }
    {
        puts("OK   Golden tests passed");
    }
}

static struct Menu MENU = {
    "Tests for pdti8 model",
    "pdti8",
    {
        MENU_ITEM('0', "Run with zeros input", do_classify_zeros),
        MENU_ITEM('1', "Run with no-person input", do_classify_no_person),
        MENU_ITEM('2', "Run with person input", do_classify_person),
        MENU_ITEM('g', "Run golden tests (check for expected outputs)", do_golden_tests),
        MENU_END,
    },
};

// For integration into menu system
void pdti8_menu()
{
    pdti8_init();
    menu_run(&MENU);
}
