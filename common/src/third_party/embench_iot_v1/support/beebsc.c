/* BEEBS local library variants

   Copyright (C) 2019 Embecosm Limited.

   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

/* These are very simple local versions of library routines, to ensure the
   code is compiled with the flags used for the benchmark.  Not all library
   routines are here, just ones that cause a lot of unecessary load, or where
   there is variation between platforms and architectures. */

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include "third_party/embench_iot_v1/support/beebsc.h"

/* Seed for the random number generator */

static long int seed = 0;

/* Heap records and sane initial values */

static void *heap_ptr = NULL;
static void *heap_end = NULL;
static size_t heap_requested = 0;


/* Yield a sequence of random numbers in the range [0, 2^15-1].

   long int is guaranteed to be at least 32 bits. The seed only ever uses 31
   bits (so is positive).

   For BEEBS this gets round different operating systems using different
   multipliers and offsets and RAND_MAX variations. */

int
rand_beebs (void)
{
  seed = (seed * 1103515245L + 12345) & ((1UL << 31) - 1);
  return (int) (seed >> 16);
}


/* Initialize the random number generator */

void
srand_beebs (unsigned int new_seed)
{
  seed = (long int) new_seed;
}


/* Initialize the BEEBS heap pointers. Note that the actual memory block is
   in the caller code. */

void
init_heap_beebs (void *heap, size_t heap_size)
{
  assert(heap_size % sizeof(void *) == 0);  /* see #138 */
  heap_ptr = (void *) heap;
  heap_end = (void *) ((char *) heap_ptr + heap_size);
  heap_requested = 0;
}


/* Report if malloc ever failed.

   Return non-zero (TRUE) if malloc did not reqest more than was available
   since the last call to init_heap_beebs, zero (FALSE) otherwise. */

int
check_heap_beebs (void *heap)
{
  return ((void *) ((char *) heap + heap_requested) <= heap_end);
}


/* BEEBS version of malloc.

   This is primarily to reduce library and OS dependencies. Malloc is
   generally not used in embedded code, or if it is, only in well defined
   contexts to pre-allocate a fixed amount of memory. So this simplistic
   implementation is just fine.

   Note in particular the assumption that memory will never be freed! */

void *
malloc_beebs (size_t size)
{
  if (size == 0)
    return NULL;

  void *next_heap_ptr = (char *)heap_ptr + size;

  heap_requested += size;

  const size_t alignment = sizeof (void *);

  /* Check if the next heap pointer is aligned, otherwise add some padding */
  if (((uintptr_t)next_heap_ptr % alignment) != 0)
    {
      size_t padding = alignment - ((uintptr_t)next_heap_ptr % alignment);

      next_heap_ptr = (char *)next_heap_ptr + padding;

      /* padding is added to heap_requested because otherwise it will break
         check_heap_beebs() */
      heap_requested += padding;
    }

  /* Check if we can "allocate" enough space */
  if (next_heap_ptr > heap_end)
    return NULL;

  void *new_ptr = heap_ptr;
  heap_ptr = next_heap_ptr;

  return new_ptr;
}


/* BEEBS version of calloc.

   Implement as wrapper for malloc */

void *
calloc_beebs (size_t nmemb, size_t size)
{
  void *new_ptr = malloc_beebs (nmemb * size);

  /* Calloc is defined to zero the memory. OK to use a function here, because
     it will be handled specially by the compiler anyway. */

  if (NULL != new_ptr)
    memset (new_ptr, 0, nmemb * size);

  return new_ptr;
}


/* BEEBS version of realloc.

   This is primarily to reduce library and OS dependencies. We just have to
   allocate new memory and copy stuff across. */

void *
realloc_beebs (void *ptr, size_t size)
{
  if (ptr == NULL)
    return NULL;

  /* Get a new aligned pointer */
  void *new_ptr = malloc_beebs (size);

  /* This is clunky, since we don't know the size of the original pointer.
     However it is a read only action and we know it must be big enough if we
     right off the end, or we couldn't have allocated here. If the size is
     smaller, it doesn't matter. */

  if (new_ptr != NULL)
    for (size_t i = 0; i < size; i++)
      ((char *)new_ptr)[i] = ((char *)ptr)[i];

  return new_ptr;
}


/* BEEBS version of free.

   For our simplified version of memory handling, free can just do nothing. */

void
free_beebs (void *ptr __attribute__ ((unused)))
{
}


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
