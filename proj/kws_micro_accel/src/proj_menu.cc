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

#include "proj_menu.h"

#include <generated/csr.h>

#include <cstdio>

#include "cfu.h"
#include "kws_cfu.h"
#include "menu.h"

namespace {

typedef struct {
  uint8_t funct3;
  uint8_t funct7;
  uint32_t rs1;
  uint32_t rs2;
  uint32_t expected;
} KwsCfuTestCase;

// Packs 4 bytes into one 32 bit value.
constexpr uint32_t pack_vals(int8_t w, int8_t x, int8_t y, int8_t z) {
  return (w << 24) | (x << 16) | (y << 8) | z;
}

KwsCfuTestCase reset() { return {0, 0, 0, 0, 0}; }

KwsCfuTestCase mac_case(uint32_t rs1, uint32_t rs2, uint32_t expected) {
  return {1, 0, rs1, rs2, expected};
}

KwsCfuTestCase mac_layer_1_case(uint32_t rs1, uint32_t rs2, uint32_t expected) {
  return {1, 2, rs1, rs2, expected};
}

KwsCfuTestCase simd_mac_case(uint32_t rs1, uint32_t rs2, uint32_t expected) {
  return {1, 1, rs1, rs2, expected};
}

// Tests hardware and software [SIMD] MAC against a set of test cases.
static void do_mac_tests() {
  bool all_passed = true;

  /* Test cases for the [SIMD] MAC. */
  static KwsCfuTestCase cases[] = {
      reset(),

      // Test empty MAC input.
      mac_case(0, 0, 0),

      // Test MAC only looks at one word
      mac_case(pack_vals(1, 1, 1, 0), pack_vals(1, 1, 1, 0), 0),

      // Test MAC multiplication and addition of input offset.
      mac_case(1, 1, 129),

      // Test MAC for layer one uses different input offset.
      mac_layer_1_case(1, 1, 47),

      reset(),

      // Test empty SIMD MAC input.
      simd_mac_case(0, 0, 0),

      // Test SIMD MAC in all words and addition of input offset.
      simd_mac_case(pack_vals(0, 0, 0, 1), pack_vals(0, 0, 0, 1), 129),
      simd_mac_case(pack_vals(0, 0, 1, 0), pack_vals(0, 0, 1, 0), 258),
      simd_mac_case(pack_vals(0, 1, 0, 0), pack_vals(0, 1, 0, 0), 387),
      simd_mac_case(pack_vals(1, 0, 0, 0), pack_vals(1, 0, 0, 0), 516),

      // Test negative result in SIMD MAC.
      simd_mac_case(0, pack_vals(-5, 0, 0, 0), -124),

      // Test max SIMD MAC input.
      simd_mac_case(pack_vals(127, 127, 127, 127),
                    pack_vals(127, 127, 127, 127), 129416),

      // Test min SIMD MAC input.
      simd_mac_case(pack_vals(127, 127, 127, 127),
                    pack_vals(-128, -128, -128, -128), 96011),
  };

  for (const auto& t : cases) {
    const uint32_t sw = cfu_op_sw(t.funct3, t.funct7, t.rs1, t.rs2);

    // Silly if statement required because cfu_op_hw is inline asm.
    uint32_t hw;
    if (t.funct7 == 0x1) {
      hw = cfu_op_hw(1, 1, t.rs1, t.rs2);
    } else if (t.funct7 == 0x2) {
      hw = cfu_op_hw(1, 2, t.rs1, t.rs2);
    } else if (t.funct3) {
      hw = cfu_op_hw(1, 0, t.rs1, t.rs2);
    } else {
      hw = cfu_op_hw(0, 0, t.rs1, t.rs2);
    }

    if (sw != hw || hw != t.expected) {
      all_passed = false;
      printf("FAIL: funct3 = %u, funct7 = %u, rs1 = %lu, rs2 = %lu.\n",
             t.funct3, t.funct7, t.rs1, t.rs2);
      printf("      Expected %lu but got: Software %lu, Hardware %lu.\n",
             t.expected, sw, hw);
    }
  }

  if (all_passed) {
    puts("PASS: All [SIMD] MAC CFU tests passed.");
  } else {
    puts("FAIL: Not all [SIMD] MAC CFU tests passed.");
  }
}

// Tests hardware arithmetic CFU ops.
static void do_arithmetic_tests() {
  bool all_passed = true;

  // For loops iterate over the delta of values seen during inference.
  for (int shift = -9; shift < -4; shift++) {
    printf("Starting shift: %d.\n", shift);
    for (int32_t top = -7737; top < 10260; top += 30) {
      for (int32_t bottom = -2146395217; bottom < 2146454171;
           bottom += 1000000) {
        int32_t sw = ROUNDING_DOUBLE_HIGH_SW(top, bottom);
        int32_t hw = ROUNDING_DOUBLE_HIGH_HW(top, bottom);
        if (sw != hw) {
          all_passed = false;
          printf("FAIL: ROUNDING_DOUBLE_HIGH(%ld, %ld).\n", top, bottom);
          printf("      Software: %ld, Hardware %ld.\n", sw, hw);
        }
        sw = ROUNDING_CLAMPING_DIVIDE_BY_POT_SW(shift);
        hw = ROUNDING_CLAMPING_DIVIDE_BY_POT_HW(shift);
        if (sw != hw) {
          all_passed = false;
          printf("FAIL: ROUNDING_CLAMPING_DIVIDE_BY_POT(%d).\n", shift);
          printf("      Software: %ld, Hardware %ld.\n", sw, hw);
        }
      }
    }
  }
  if (all_passed) {
    puts("PASS: All arithmetic CFU tests passed.");
  } else {
    puts("FAIL: Not all arithmetic CFU tests passed.");
  }
}

static void perform_setup() {
#ifdef CSR_SPIFLASH_PHY_BASE
  puts("Setting SPI divisor.");
  spiflash_phy_clk_divisor_write(0);
#endif  // CSR_SPIFLASH_PHY_BASE
}

struct Menu MENU = {
    "Project Menu",
    "kws_micro_accel",
    {
        MENU_ITEM('s', "Peform Setup", perform_setup),
        MENU_ITEM('m', "Run [SIMD] MAC CFU Tests", do_mac_tests),
        MENU_ITEM('a', "Run Arithmetic CFU Tests", do_arithmetic_tests),
        MENU_END,
    },
};

};  // anonymous namespace

extern "C" void do_proj_menu() { menu_run(&MENU); }
