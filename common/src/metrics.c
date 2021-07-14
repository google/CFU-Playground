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

#include "metrics.h"

#include <stdint.h>
#include <generated/csr.h>

void get_csr_metrics(uint32_t *acc, uint32_t *refill, uint32_t *stall) {
  __asm__ volatile ("csrr %0, %1" : "=r"(*acc) : "i"(CSR_ACC_COUNTER));
  __asm__ volatile ("csrr %0, %1" : "=r"(*refill) : "i"(CSR_REFILL_COUNTER));
  __asm__ volatile ("csrr %0, %1" : "=r"(*stall) : "i"(CSR_STALL_COUNTER));
}

void set_flash_control(uint32_t val) {
#ifdef LITESPI_CS_COUNTER
  spi_flash_counter_control_write(val);
#endif
}

void spi_flash_counter_prepare(void) {
#ifdef LITESPI_CS_COUNTER
  spi_flash_counter_control_reset_write(0);
  spi_flash_counter_control_enable_write(1);
#endif
}

void spi_flash_counter_stop(void) {
#ifdef LITESPI_CS_COUNTER
  spi_flash_counter_control_reset_write(0);
  spi_flash_counter_control_enable_write(0);
#endif
}

void spi_flash_counter_restart(void) {
#ifdef LITESPI_CS_COUNTER
  spi_flash_counter_control_reset_write(1);
  spi_flash_counter_control_enable_write(0);
#endif
}

void spi_flash_counter_print_ticks(void) {
#ifdef LITESPI_CS_COUNTER
  uint32_t cs = spi_flash_counter_cs_ticks_read();
  uint32_t clk = spi_flash_counter_clk_ticks_read();

  printf("[CS active] %zu out of %zu cycles\n", cs, clk);
#else
  printf("[CS active] SPI flash activity counter not present in the SoC\n");
#endif
}
