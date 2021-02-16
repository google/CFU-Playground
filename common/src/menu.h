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


#ifndef MENU_H
#define MENU_H
#include <stdbool.h>


struct MenuItem {
    const char selection;
    const char *description;
    const void (*fn)(void);
    const bool exit;
};

struct Menu {
    const char *title;
    const char *prompt;
    struct MenuItem items[];
};

#define MENU_ITEM(selection, description, fn) {selection, description, fn, false}

// Last item in a non-top level menu
#define MENU_END {'x', 'eXit to previous menu', NULL, true}, MENU_SENTINEL

// Last item in a top level menu
#define MENU_SENTINEL {'\0', NULL, NULL, false}

// Run a menu
void menu_run(struct Menu *menu);

#endif // MENU_H