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
#include "models/mnv2/mnv2.h"
#include "tflite.h"
#include "menu.h"

#include "models/mnv2/model_mobilenetv2_160_035.h"

// Initialize everything once
// deallocate tensors when done
static void mnv2_init(void)
{
    tflite_load_model(model_mobilenetv2_160_035);
}

// Run classification, after input has been loaded
static int32_t mnv2_classify()
{
    printf("Running mnv2\n");
    tflite_classify();

    // Process the inference results.
    int8_t *output = tflite_get_output();
    return output[1] - output[0];
}

static void do_classify_zeros()
{
    tflite_set_input_zeros();
    mnv2_classify();
}

static struct Menu MENU = {
    "Tests for mnv2 model",
    "mnv2",
    {
        MENU_ITEM('1', "Run with zeros input", do_classify_zeros),
        MENU_END,
    },
};

// For integration into menu system
void mnv2_menu()
{
    mnv2_init();
    menu_run(&MENU);
}
