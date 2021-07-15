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

#ifndef METRICS_H
#define METRICS_H
//#include <generated/mem.h>
#include <stdint.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CSR_ACC_COUNTER     0xcc4
#define CSR_REFILL_COUNTER  0xcc8
#define CSR_STALL_COUNTER   0xccc

void get_csr_metrics(uint32_t *acc, uint32_t *refill, uint32_t *stall);

#define DCACHE_SETUP_METRICS \
  uint32_t acc_pre, refill_pre, stall_pre, acc_cnt, refill_cnt, stall_cnt; \
  get_csr_metrics(&acc_pre, &refill_pre, &stall_pre)

#define DCACHE_PRINT_METRICS \
  do { \
    get_csr_metrics(&acc_cnt, &refill_cnt, &stall_cnt); \
    printf("[Dcache accesses] Before: %lu, After: %lu, Diff: %lu\n", \
           acc_pre, acc_cnt, acc_cnt - acc_pre); \
    printf("[Dcache refills]  Before: %lu, After: %lu, Diff: %lu\n", \
           refill_pre, refill_cnt, refill_cnt - refill_pre); \
    printf("[Dcache stalls]   Before: %lu, After: %lu, Diff: %lu\n", \
           stall_pre, stall_cnt, stall_cnt - stall_pre); \
  } while (0)

void spi_flash_counter_prepare(void);
void spi_flash_counter_stop(void);
void spi_flash_counter_restart(void);
void spi_flash_counter_print_ticks(void);

#define FLASH_SETUP_METRICS \
  spi_flash_counter_prepare()

#define FLASH_PRINT_METRICS \
  do { \
    spi_flash_counter_stop(); \
    spi_flash_counter_print_ticks(); \
    spi_flash_counter_restart(); \
  } while (0)

#define PERF_SETUP_METRICS \
    DCACHE_SETUP_METRICS; \
    FLASH_SETUP_METRICS

#define PERF_PRINT_METRICS \
    DCACHE_PRINT_METRICS; \
    FLASH_PRINT_METRICS
  
#ifdef __cplusplus
}
#endif
#endif  // METRICS_H
