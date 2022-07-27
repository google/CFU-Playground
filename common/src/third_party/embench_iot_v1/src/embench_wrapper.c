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

#define EMBENCH_WRAPPER(benchname) \
void embench_wrapper_##benchname () \
{ \
  volatile int result; \
  int correct; \
  initialise_benchmark_##benchname (); \
  warm_caches_##benchname (WARMUP_HEAT); \
  unsigned int start = perf_get_mcycle(); \
  result = benchmark_##benchname (); \
  unsigned int end = perf_get_mcycle(); \
  correct = verify_benchmark_##benchname (result); \
  printf("%s\n", correct ? "OK  Benchmark result verified" : "FAIL  Benchmark result incorrect"); \
  printf("Spent %u cycles\n", end - start); \
}

#if defined(INCLUDE_EMBENCH_PRIMECOUNT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(primecount)
#endif
#if defined(INCLUDE_EMBENCH_MINVER) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER(minver)
#endif

