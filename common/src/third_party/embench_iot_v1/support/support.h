/* Support header for BEEBS.

   Copyright (C) 2014 Embecosm Limited and the University of Bristol
   Copyright (C) 2019 Embecosm Limited

   Contributor James Pallister <james.pallister@bristol.ac.uk>

   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

#ifndef SUPPORT_H
#define SUPPORT_H

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "third_party/embench_iot_v1/support/boardsupport.h"

/* Benchmarks must implement verify_benchmark, which must return -1 if no
   verification is done. */

#define VERIFY_BENCH(benchname) \
int verify_benchmark_##benchname (int result);

/* Standard functions implemented for each board */

void initialise_board (void);
void start_trigger (void);
void stop_trigger (void);

/* Every benchmark implements this for one-off data initialization.  This is
   only used for initialization that is independent of how often benchmark ()
   is called. */

#define INIT_BENCHMARK(benchname) \
void initialise_benchmark_##benchname (void);

/* Every benchmark implements this for cache warm up, typically calling
   benchmark several times. The argument controls how much warming up is
   done, with 0 meaning no warming. */

#define WARM_CACHES(benchname) \
void warm_caches_##benchname (int temperature);

/* Every benchmark implements this as its entry point. Don't allow it to be
   inlined! */

#define BENCHMARK(benchname) \
int benchmark_##benchname (void) __attribute__ ((noinline));

/* Every benchmark must implement this to validate the result of the
   benchmark. */

#define VERIFY_BENCHMARK(benchname) \
int verify_benchmark_##benchname (int res);

#define BENCHMARK_FUNCTIONS(benchname) \
INIT_BENCHMARK(benchname) \
WARM_CACHES(benchname) \
BENCHMARK(benchname) \
VERIFY_BENCHMARK(benchname) 

#if defined(INCLUDE_EMBENCH_PRIMECOUNT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(primecount)
#endif
#if defined(INCLUDE_EMBENCH_MINVER) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(minver)
#endif
#if defined(INCLUDE_EMBENCH_AHA_MONT64) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(aha_mont64)
#endif
#if defined(INCLUDE_EMBENCH_CRC_32) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(crc_32)
#endif
#if defined(INCLUDE_EMBENCH_CUBIC) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(cubic)
#endif
#if defined(INCLUDE_EMBENCH_EDN) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(edn)
#endif
#if defined(INCLUDE_EMBENCH_HUFFBENCH) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(huffbench)
#endif
#if defined(INCLUDE_EMBENCH_MATMUL) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(matmul)
#endif
#if defined(INCLUDE_EMBENCH_MD5) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(md5)
#endif
#if defined(INCLUDE_EMBENCH_NBODY) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(nbody)
#endif
#if defined(INCLUDE_EMBENCH_NETTLE_AES) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(nettle_aes)
#endif
#if defined(INCLUDE_EMBENCH_NETTLE_SHA256) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(nettle_sha256)
#endif
#if defined(INCLUDE_EMBENCH_NSICHNEU) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(nsichneu)
#endif
#if defined(INCLUDE_EMBENCH_QRDUINO) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(qrduino)
#endif
#if defined(INCLUDE_EMBENCH_SLRE) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(slre)
#endif
#if defined(INCLUDE_EMBENCH_ST) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(st)
#endif
#if defined(INCLUDE_EMBENCH_STATEMATE) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(statemate)
#endif
#if defined(INCLUDE_EMBENCH_TARFIND) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(tarfind)
#endif
#if defined(INCLUDE_EMBENCH_UD) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(ud)
#endif
#if defined(INCLUDE_EMBENCH_WIKISORT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
BENCHMARK_FUNCTIONS(wikisort)
#endif

/* Local simplified versions of library functions */

#include "third_party/embench_iot_v1/support/beebsc.h"

#endif /* SUPPORT_H */

/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
