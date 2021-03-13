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
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Defines an item in a menu
struct MenuItem {
  // Character used to select the item
  const char selection;
  // Description of the item in the menu
  const char* description;
  // The function that implements the menu item
  void (*const fn)(void);
  // Used to exit from submenus
  const bool exit;
};

// Defines a menu
struct Menu {
  // The title of the menu
  const char* title;
  // String to use in the prompt
  const char* prompt;
  // The menu choices
  struct MenuItem items[];
};

#define MENU_ITEM(selection, description, fn) \
  { selection, description, fn, false }

// Last items in a non-top level menu
#define MENU_END {'x', "eXit to previous menu", NULL, true}, MENU_SENTINEL

// Last item in a top level menu
#define MENU_SENTINEL \
  { '\0', NULL, NULL, false }

// Run a menu
void menu_run(struct Menu* menu);

#ifdef __cplusplus
}
#endif
#endif  // MENU_H