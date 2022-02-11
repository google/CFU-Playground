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
#include <crc.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <stdio.h>

#include "menu.h"
#include "perf.h"
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

// We compute the checksum of an arbitrarily chosen region later in flash,
// which is unlikely to hold the bitstream or any other important data,
// so that you can pre-fill it with some chosen values and then compare the
// checksum produced by different versions of the bitstream (expecting the
// checksum to be the same each time).
#define CHECKSUM_REGION_OFFSET (4*1024*1024)
#define CHECKSUM_REGION_LENGTH (256*1024)
static void checksum_spiflash(void) {
  printf("Computing CRC32 of SPI flash region 0x%08x-0x%08x: ",
         CHECKSUM_REGION_OFFSET,
         CHECKSUM_REGION_OFFSET + CHECKSUM_REGION_LENGTH);
  unsigned int crc = crc32(
    (unsigned char *)(SPIFLASH_BASE + CHECKSUM_REGION_OFFSET),
    CHECKSUM_REGION_LENGTH);
  printf("%08x\n\n", crc);
}

// The intention here is to catch problems with consecutive SPI command cycles,
// for example CS inactive time too short.
static void test_spiflash_nonsequential_access(void) {
  unsigned int start = perf_get_mcycle();
  uint32_t val = *(volatile uint32_t *)SPIFLASH_BASE;
  // Now access another address elsewhere to force a new SPI command cycle.
  *(volatile uint32_t *)(SPIFLASH_BASE + 1024);
  // Now go back and load the original value in a new SPI command cycle.
  // It should match.
  uint32_t val2 = *(volatile uint32_t *)SPIFLASH_BASE;
  unsigned int end = perf_get_mcycle();
  printf("Spent %u cycles\n", end - start);
  if (val == 0xff || val2 == 0xff)
    // 0xff may indicate a failed read
    printf("%08x == %08x  SEEMS SUPICIOUS\n", val, val2);
  else if (val == val2)
    printf("%08x == %08x  OK\n", val, val2);
  else
    printf("%08x != %08x  NOT OK\n", val, val2);
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
    MENU_ITEM('c', "CRC32 checksum", checksum_spiflash),
    MENU_ITEM('n', "non-sequential access test", test_spiflash_nonsequential_access),
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
