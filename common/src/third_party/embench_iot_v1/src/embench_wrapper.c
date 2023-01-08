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

#include "third_party/embench_iot_v1/support/support.h"
#include "perf.h"
#include <stdio.h>
#include "generated/csr.h"


#ifdef USE_LITEX_TIMER
#define TIMER_TYPE    uint64_t
#define RESET_TIMER() perf_reset_litex_timer()
#define GET_TIMER()   perf_get_litex_timer()
#define PRINT_PERF(a, b)  printf("Spent %llu cycles\n", a - b) 
#else // default timer to use is mcycle
#define TIMER_TYPE    unsigned int
#define RESET_TIMER() /* no reset for mcycle */
#define GET_TIMER()   perf_get_mcycle() 
#define PRINT_PERF(a, b)  printf("Spent %u cycles\n", b - a) 
#endif


#define EMBENCH_WRAPPER(benchname) \
void embench_wrapper_##benchname () \
{ \
  volatile int result; \
  int correct; \
  initialise_benchmark_##benchname (); \
  warm_caches_##benchname (WARMUP_HEAT); \
  RESET_TIMER(); \
  TIMER_TYPE start = GET_TIMER(); \
  result = benchmark_##benchname (); \
  TIMER_TYPE end = GET_TIMER(); \
  correct = verify_benchmark_##benchname (result); \
  printf("%s\n", correct ? "OK  Benchmark result verified" : "FAIL  Benchmark result incorrect"); \
  PRINT_PERF(start, end); \
}


#if defined(INCLUDE_EMBENCH_PRIMECOUNT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(primecount)
#endif
#if defined(INCLUDE_EMBENCH_MINVER) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(minver)
#endif
#if defined(INCLUDE_EMBENCH_AHA_MONT64) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(aha_mont64)
#endif
#if defined(INCLUDE_EMBENCH_CRC_32) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(crc_32)
#endif
#if defined(INCLUDE_EMBENCH_CUBIC) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(cubic)
#endif
#if defined(INCLUDE_EMBENCH_EDN) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(edn)
#endif
#if defined(INCLUDE_EMBENCH_HUFFBENCH) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(huffbench)
#endif
#if defined(INCLUDE_EMBENCH_MATMUL) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(matmul)
#endif
#if defined(INCLUDE_EMBENCH_MD5) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(md5)
#endif
#if defined(INCLUDE_EMBENCH_NBODY) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(nbody)
#endif
#if defined(INCLUDE_EMBENCH_NETTLE_AES) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(nettle_aes)
#endif
#if defined(INCLUDE_EMBENCH_NETTLE_SHA256) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(nettle_sha256)
#endif
#if defined(INCLUDE_EMBENCH_NSICHNEU) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(nsichneu)
#endif
#if defined(INCLUDE_EMBENCH_QRDUINO) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(qrduino)
#endif
#if defined(INCLUDE_EMBENCH_SLRE) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(slre)
#endif
#if defined(INCLUDE_EMBENCH_ST) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(st)
#endif
#if defined(INCLUDE_EMBENCH_STATEMATE) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(statemate)
#endif
#if defined(INCLUDE_EMBENCH_TARFIND) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(tarfind)
#endif
#if defined(INCLUDE_EMBENCH_UD) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(ud)
#endif
#if defined(INCLUDE_EMBENCH_WIKISORT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(wikisort)
#endif

