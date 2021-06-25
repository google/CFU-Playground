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
#include <stdio.h>

#include "menu.h"
#include "spiflash.h"

#ifdef SPIFLASH_BASE

#define BYTES_PER_LINE 16
#define LINES_PER_PAGE 24
static void dump_spiflash(void) {
  char *base = (char *)SPIFLASH_BASE;
  size_t line_offset = 0;
  do {
    printf("\n0x%08p  ", base + line_offset);
    for (size_t i = 0; i < BYTES_PER_LINE; i++)
      printf("%02x ", base[line_offset + i]);
    printf("   ");
    for (size_t i = 0; i < BYTES_PER_LINE; i++) {
      char c = base[line_offset + i];
      putchar((c < 0x20 || c > 0x7e) ? '.' : c);
    }

    line_offset += BYTES_PER_LINE;

    // Give the user a chance to bail out every now and then
    if (line_offset % (BYTES_PER_LINE * LINES_PER_PAGE) == 0) {
      printf("\n\nContinue? (y/n) ");
      if (readchar() != 'y')
        break;
      printf("\n");
    }
  } while (line_offset <= SPIFLASH_SIZE - BYTES_PER_LINE);
}

#ifdef CSR_SPIFLASH_PHY_BASE
static void do_set_spiflash_div(void) {
  unsigned int div = spiflash_phy_clk_divisor_read();
  printf("Current clock divisor: %d\n", div);
  printf("Enter clock divisor (0-9):\n");
  char c = readchar();
  putchar(c);
  if (c < '0') return;
  if (c > '9') return;
  spiflash_phy_clk_divisor_write((uint32_t)(c - '0'));
  div = spiflash_phy_clk_divisor_read();
  printf("New clock divisor: %d\n", div);
}
#endif // CSR_SPIFLASH_PHY_BASE

static struct Menu MENU = {
  "SPI Flash Debugging Menu",
  "spiflash",
  {
    MENU_ITEM('d', "dump flash contents", dump_spiflash),
#ifdef CSR_SPIFLASH_PHY_BASE
    MENU_ITEM('s', "set clock divisor", do_set_spiflash_div),
#endif
    MENU_END,
  },
};

void spiflash_menu(void) {
  menu_run(&MENU);
}

#else // SPIFLASH_BASE

// Everything compiled out when we don't have SPI flash.

void spiflash_menu(void) { }

#endif
