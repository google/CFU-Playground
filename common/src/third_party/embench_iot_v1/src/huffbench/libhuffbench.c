/* BEEBS cover benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later

   Original version by Scott Robert Ladd

    huffbench
    Standard C version
    17 April 2003

    Written by Scott Robert Ladd (scott@coyotegulch.com)
    No rights reserved. This is public domain software, for use by anyone.

    A data compression benchmark that can also be used as a fitness test
    for evolving optimal compiler options via genetic algorithm.

    This program implements the Huffman compression algorithm. The code
    is not the tightest or fastest possible C code; rather, it is a
    relatively straight-forward implementation of the algorithm,
    providing opportunities for an optimizer to "do its thing."

    Note that the code herein is design for the purpose of testing
    computational performance; error handling and other such "niceties"
    is virtually non-existent.

    Actual benchmark results can be found at:
            http://www.coyotegulch.com

    Please do not use this information or algorithm in any way that might
    upset the balance of the universe or otherwise cause the creation of
    singularities.

*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdbool.h>
#include <math.h>

#include "third_party/embench_iot_v1/support/support.h"

/* This scale factor will be changed to equalise the runtime of the
   benchmarks. */
#define LOCAL_SCALE_FACTOR 11

/* BEEBS heap is just an array */

#define HEAP_SIZE 8192
static char heap[HEAP_SIZE] __attribute__((aligned));

#define TEST_SIZE 500

typedef unsigned long bits32;
typedef unsigned char byte;

// compressed (encoded) data

static const byte orig_data[TEST_SIZE] = {
  'J', '2', 'O', 'Z', 'F', '5', '0', 'F', 'Y', 'L',
  'D', '5', 'U', 'T', 'V', 'Y', 'Y', 'R', 'M', 'T',
  '0', 'V', 'X', 'O', '0', '1', 'V', 'C', '5', 'F',
  'N', 'I', 'B', '1', 'C', 'G', '1', '2', 'M', 'T',
  'I', 'P', 'T', '2', 'C', 'I', 'V', '0', '0', 'B',
  'O', 'U', 'W', 'F', 'D', 'R', 'A', 'Y', 'T', 'A',
  '3', 'A', 'I', '4', '2', 'K', 'F', 'X', 'H', 'R',
  'K', 'P', 'A', '3', 'L', 'C', 'G', 'A', '3', 'A',
  'B', 'L', 'U', 'Y', 'Q', 'X', 'J', 'R', 'Q', '2',
  'R', 'N', '2', 'Z', 'M', 'Y', 'E', 'R', 'P', 'L',
  'C', '0', '0', 'C', 'X', 'F', 'E', '3', 'G', 'B',
  '3', 'H', 'M', 'S', '5', '3', 'J', 'I', 'O', 'Z',
  'E', '5', 'H', 'B', 'Y', 'T', 'Z', '2', 'E', 'J',
  'H', 'G', 'D', 'B', 'I', '0', 'H', 'M', 'Y', 'N',
  'O', 'V', 'U', '0', 'H', 'U', 'X', 'R', '2', 'F',
  'K', 'B', 'E', 'R', 'C', '3', 'E', '1', 'Z', 'I',
  'E', 'B', 'O', 'H', 'C', 'W', 'C', 'J', 'D', '0',
  'W', 'R', 'P', 'L', 'L', 'X', '5', 'D', 'I', '1',
  'I', 'S', '2', 'N', 'E', '4', 'K', 'I', '0', 'D',
  'R', '4', 'E', '5', 'G', 'H', 'W', 'I', 'Q', 'Z',
  'C', 'H', 'K', 'R', 'S', 'V', 'I', 'R', 'Y', 'Q',
  'M', 'B', 'D', 'J', 'O', 'H', 'H', 'Y', 'P', 'B',
  '1', 'A', 'A', 'A', 'A', 'G', 'H', 'W', 'O', 'X',
  'P', 'Q', '4', 'Z', 'B', 'Q', 'O', 'K', 'B', 'H',
  '0', 'O', 'I', '3', 'X', 'W', 'E', '4', 'O', 'U',
  'A', 'J', 'U', 'A', 'J', 'U', 'G', 'Q', 'K', 'U',
  'I', 'Z', 'E', 'G', 'S', 'F', 'X', 'B', 'P', 'Y',
  'I', 'K', 'G', 'Q', 'H', '3', 'G', 'M', '2', 'U',
  'A', '2', '3', 'U', '2', 'H', 'J', 'C', 'X', 'T',
  'W', '5', 'N', '0', 'G', '5', '5', '3', 'A', 'P',
  'V', 'I', 'Z', '2', 'Y', 'A', 'Z', '4', 'M', 'V',
  'S', 'M', 'R', 'Q', 'B', 'N', 'X', 'K', 'P', 'O',
  '3', 'F', 'O', 'K', '5', 'U', 'K', '5', 'R', 'K',
  'O', 'G', 'T', 'H', 'C', 'L', 'H', '2', 'K', 'U',
  'R', '2', 'A', 'D', 'M', 'B', 'Q', 'D', 'L', 'A',
  'S', 'J', 'F', 'A', 'T', 'F', 'U', '3', 'E', 'F',
  'I', 'S', 'L', '1', 'Z', 'O', 'G', 'A', 'K', 'Q',
  'U', '1', 'N', 'V', '4', 'Z', 'W', 'P', '3', 'C',
  'P', 'P', 'L', 'U', 'P', '4', 'Z', 'D', '2', '3',
  'I', 'E', 'P', 'T', '5', 'I', 'B', 'F', 'J', 'L',
  'W', '3', 'H', 'D', 'S', 'F', '2', 'J', 'U', 'Z',
  'L', 'D', 'I', 'W', 'Y', 'X', 'U', 'R', '0', 'Q',
  'P', 'C', 'U', '4', 'W', 'T', 'H', 'X', 'Z', 'Q',
  'D', 'P', 'N', 'K', 'S', 'A', 'P', 'O', 'J', 'E',
  'I', 'U', 'H', 'Q', 'K', '5', 'I', '4', 'R', 'C',
  'P', 'A', 'F', 'D', '4', '1', 'X', 'F', 'S', 'Q',
  'V', 'V', '5', 'D', '5', 'R', 'D', 'P', '5', 'M',
  'T', 'H', 'A', '0', 'Y', 'K', '0', 'A', 'I', 'L',
  'C', 'X', 'L', 'H', '1', 'J', 'C', 'S', 'P', 'V',
  'C', 'E', 'K', 'B', 'H', 'K', 'S', 'K', 'Z', 'R' };

static byte test_data[TEST_SIZE];


// utility function for processing compression trie
static void
heap_adjust (size_t * freq, size_t * local_heap, int n, int k)
{
  // this function compares the values in the array
  // 'freq' to order the elements of 'heap' according
  // in an inverse heap. See the chapter on priority
  // queues and heaps for more explanation.
  int j;

  --local_heap;

  int v = local_heap[k];

  while (k <= (n / 2))
    {
      j = k + k;

      if ((j < n) && (freq[local_heap[j]] > freq[local_heap[j + 1]]))
	++j;

      if (freq[v] < freq[local_heap[j]])
	break;

      local_heap[k] = local_heap[j];
      k = j;
    }

  local_heap[k] = v;
}

// Huffman compression/decompression function
void
compdecomp (byte * data, size_t data_len)
{
  size_t i, j, n, mask;
  bits32 k, t;
  byte c;
  byte *cptr;
  byte *dptr = data;

  /*
     COMPRESSION
   */

  // allocate data space
  byte *comp = (byte *) malloc_beebs (data_len + 1);

  size_t freq[512];		// allocate frequency table
  size_t heap1[256];		// allocate heap
  int link[512];		// allocate link array
  bits32 code[256];		// huffman codes
  byte clen[256];		// bit lengths of codes

  memset (comp, 0, sizeof (byte) * (data_len + 1));
  memset (freq, 0, sizeof (size_t) * 512);
  memset (heap1, 0, sizeof (size_t) * 256);
  memset (link, 0, sizeof (int) * 512);
  memset (code, 0, sizeof (bits32) * 256);
  memset (clen, 0, sizeof (byte) * 256);

  // count frequencies
  for (i = 0; i < data_len; ++i)
    {
      ++freq[(size_t) (*dptr)];
      ++dptr;
    }

  // create indirect heap based on frequencies
  n = 0;

  for (i = 0; i < 256; ++i)
    {
      if (freq[i])
	{
	  heap1[n] = i;
	  ++n;
	}
    }

  for (i = n; i > 0; --i)
    heap_adjust (freq, heap1, n, i);

  // generate a trie from heap
  size_t temp;

  // at this point, n contains the number of characters
  // that occur in the data array
  while (n > 1)
    {
      // take first item from top of heap
      --n;
      temp = heap1[0];
      heap1[0] = heap1[n];

      // adjust the heap to maintain properties
      heap_adjust (freq, heap1, n, 1);

      // in upper half of freq array, store sums of
      // the two smallest frequencies from the heap
      freq[256 + n] = freq[heap1[0]] + freq[temp];
      link[temp] = 256 + n;	// parent
      link[heap1[0]] = -256 - n;	// left child
      heap1[0] = 256 + n;	// right child

      // adjust the heap again
      heap_adjust (freq, heap1, n, 1);
    }

  link[256 + n] = 0;

  // generate codes
  size_t m, x, maxx = 0, maxi = 0;
  int l;

  for (m = 0; m < 256; ++m)
    {
      if (!freq[m])		// character does not occur
	{
	  code[m] = 0;
	  clen[m] = 0;
	}
      else
	{
	  i = 0;		// length of current code
	  j = 1;		// bit being set in code
	  x = 0;		// code being built
	  l = link[m];		// link in trie

	  while (l)		// while not at end of trie
	    {
	      if (l < 0)	// left link (negative)
		{
		  x += j;	// insert 1 into code
		  l = -l;	// reverse sign
		}

	      l = link[l];	// move to next link
	      j <<= 1;		// next bit to be set
	      ++i;		// increment code length
	    }

	  code[m] = (unsigned long) x;	// save code
	  clen[m] = (unsigned char) i;	// save code len

	  // keep track of biggest key
	  if (x > maxx)
	    maxx = x;

	  // keep track of longest key
	  if (i > maxi)
	    maxi = i;
	}
    }

  // make sure longest codes fit in unsigned long-bits
  if (maxi > (sizeof (unsigned long) * 8))
    {
      return;
    }

  // encode data
  size_t comp_len = 0;		// number of data_len output
  char bout = 0;		// byte of encoded data
  int bit = -1;			// count of bits stored in bout
  dptr = data;

  // watch for one-value file!
  if (maxx == 0)
    {
      return;
    }

  for (j = 0; j < data_len; ++j)
    {
      // start copying at first bit of code
      mask = 1 << (clen[(*dptr)] - 1);

      // copy code bits
      for (i = 0; i < clen[(*dptr)]; ++i)
	{
	  if (bit == 7)
	    {
	      // store full output byte
	      comp[comp_len] = bout;
	      ++comp_len;

	      // check for output longer than input!
	      if (comp_len == data_len)
		{
		  return;
		}

	      bit = 0;
	      bout = 0;
	    }
	  else
	    {
	      // move to next bit
	      ++bit;
	      bout <<= 1;
	    }

	  if (code[(*dptr)] & mask)
	    bout |= 1;

	  mask >>= 1;
	}

      ++dptr;
    }

  // output any incomplete data_len and bits
  bout <<= (7 - bit);
  comp[comp_len] = bout;
  ++comp_len;

  // printf("data len = %u\n",data_len);
  // printf("comp len = %u\n",comp_len);

  /*
     DECOMPRESSION
   */

  // allocate heap2
  bits32 heap2[256];

  // allocate output character buffer
  char outc[256];

  // initialize work areas
  memset (heap2, 0, 256 * sizeof (bits32));

  // create decode table as trie heap2
  char *optr = outc;

  for (j = 0; j < 256; ++j)
    {
      (*optr) = (char) j;
      ++optr;

      // if code exists for this byte
      if (code[j] | clen[j])
	{
	  // begin at first code bit
	  k = 0;
	  mask = 1 << (clen[j] - 1);

	  // find proper node, using bits in
	  // code as path.
	  for (i = 0; i < clen[j]; ++i)
	    {
	      k = k * 2 + 1;	// right link

	      if (code[j] & mask)
		++k;		// go left

	      mask >>= 1;	// next bit
	    }

	  heap2[j] = k;		// store link in heap2
	}
    }

  // sort outc based on heap2
  for (i = 1; i < 256; ++i)
    {
      t = heap2[i];
      c = outc[i];
      j = i;

      while ((j) && (heap2[j - 1] > t))
	{
	  heap2[j] = heap2[j - 1];
	  outc[j] = outc[j - 1];
	  --j;
	}

      heap2[j] = t;
      outc[j] = c;
    }

  // find first character in table
  for (j = 0; heap2[j] == 0; ++j);

  // decode data
  k = 0;			// link in trie
  i = j;
  mask = 0x80;
  n = 0;
  cptr = comp;
  dptr = data;

  while (n < data_len)
    {
      k = k * 2 + 1;		// right link

      if ((*cptr) & mask)
	++k;			// left link if bit on

      // search heap2 until link >= k
      while (heap2[i] < k)
	++i;

      // code matches, character found
      if (k == heap2[i])
	{
	  (*dptr) = outc[i];
	  ++dptr;
	  ++n;
	  k = 0;
	  i = j;
	}

      // move to next bit
      if (mask > 1)
	mask >>= 1;
      else			// code extends into next byte
	{
	  mask = 0x80;
	  ++cptr;
	}
    }

  // remove work areas
  free_beebs (comp);
}


int
verify_benchmark_huffbench (int res __attribute ((unused)))
{
  return 0 == memcmp (test_data, orig_data, TEST_SIZE * sizeof (orig_data[0]));
}


void
initialise_benchmark_huffbench (void)
{
}


static int benchmark_body_huffbench (int rpt);

void
warm_caches_huffbench (int heat)
{
  benchmark_body_huffbench (heat);

  return;
}


int
benchmark_huffbench (void)
{
  return benchmark_body_huffbench (LOCAL_SCALE_FACTOR * CPU_MHZ);
}


static int __attribute__ ((noinline)) benchmark_body_huffbench (int rpt)
{
  int j;

  for (j = 0; j < rpt; j++)
    {
      init_heap_beebs ((void *) heap, HEAP_SIZE);

      // initialization
      memcpy (test_data, orig_data, TEST_SIZE * sizeof (orig_data[0]));

      // what we're timing
      compdecomp (test_data, TEST_SIZE);
    }

  // done
  return 0;
}
