/* BEEBS wikisort benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later

   Originally from https://github.com/BonzaiThePenguin/WikiSort and placed
   into public domain. */

#include <string.h>

/* This scale factor will be changed to equalise the runtime of the
   benchmarks. */
#define LOCAL_SCALE_FACTOR 1

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>
#include <limits.h>

#include "third_party/embench_iot_v1/support/support.h"

/* various #defines for the C code */
#ifndef true
#define true 1
#define false 0
typedef uint8_t bool;
#endif

#define Var(name, value, type) type name = value

long
Min (const long a, const long b)
{
  if (a < b)
    return a;
  return b;
}

long
Max (const long a, const long b)
{
  if (a > b)
    return a;
  return b;
}


/* structure to test stable sorting (index will contain its original index in the array, to make sure it doesn't switch places with other items) */
typedef struct
{
  int value;
  int index;
} Test;

bool
TestCompare (Test item1, Test item2)
{
  return (item1.value < item2.value);
}

typedef bool (*Comparison) (Test, Test);



/* structure to represent ranges within the array */
typedef struct
{
  long start;
  long end;
} Range;

long
Range_length (Range range)
{
  return range.end - range.start;
}

Range
MakeRange (const long start, const long end)
{
  Range range;
  range.start = start;
  range.end = end;
  return range;
}

typedef long int (* TestCasePtr)(long int, long int);

/* toolbox functions used by the sorter */

/* swap value1 and value2 */
#define Swap(value1, value2, type) { \
	Var(a, &(value1), type*); \
	Var(b, &(value2), type*); \
	\
	Var(c, *a, type); \
	*a = *b; \
	*b = c; \
}

/* 63 -> 32, 64 -> 64, etc. */
/* apparently this comes from Hacker's Delight? */
long
FloorPowerOfTwo (const long value)
{
  long x = value;
  x = x | (x >> 1);
  x = x | (x >> 2);
  x = x | (x >> 4);
  x = x | (x >> 8);
  x = x | (x >> 16);
#if __LP64__
  x = x | (x >> 32);
#endif
  return x - (x >> 1);
}

/* find the index of the first value within the range that is equal to array[index] */
long
BinaryFirst (const Test array[], const long index, const Range range,
	     const Comparison compare)
{
  long start = range.start, end = range.end - 1;
  while (start < end)
    {
      long mid = start + (end - start) / 2;
      if (compare (array[mid], array[index]))
	start = mid + 1;
      else
	end = mid;
    }
  if (start == range.end - 1 && compare (array[start], array[index]))
    start++;
  return start;
}

/* find the index of the last value within the range that is equal to array[index], plus 1 */
long
BinaryLast (const Test array[], const long index, const Range range,
	    const Comparison compare)
{
  long start = range.start, end = range.end - 1;
  while (start < end)
    {
      long mid = start + (end - start) / 2;
      if (!compare (array[index], array[mid]))
	start = mid + 1;
      else
	end = mid;
    }
  if (start == range.end - 1 && !compare (array[index], array[start]))
    start++;
  return start;
}

/* n^2 sorting algorithm used to sort tiny chunks of the full array */
void
InsertionSort (Test array[], const Range range, const Comparison compare)
{
  long i;
  for (i = range.start + 1; i < range.end; i++)
    {
      const Test temp = array[i];
      long j;
      for (j = i; j > range.start && compare (temp, array[j - 1]); j--)
	array[j] = array[j - 1];
      array[j] = temp;
    }
}

/* reverse a range within the array */
void
Reverse (Test array[], const Range range)
{
  long index;
  for (index = Range_length (range) / 2 - 1; index >= 0; index--)
    Swap (array[range.start + index], array[range.end - index - 1], Test);
}

/* swap a series of values in the array */
void
BlockSwap (Test array[], const long start1, const long start2,
	   const long block_size)
{
  long index;
  for (index = 0; index < block_size; index++)
    Swap (array[start1 + index], array[start2 + index], Test);
}

/* rotate the values in an array ([0 1 2 3] becomes [1 2 3 0] if we rotate by 1) */
void
Rotate (Test array[], const long amount, const Range range, Test cache[],
	const long cache_size)
{
  long split;
  Range range1, range2;

  if (Range_length (range) == 0)
    return;

  if (amount >= 0)
    split = range.start + amount;
  else
    split = range.end + amount;

  range1 = MakeRange (range.start, split);
  range2 = MakeRange (split, range.end);

  /* if the smaller of the two ranges fits into the cache, it's *slightly* faster copying it there and shifting the elements over */
  if (Range_length (range1) <= Range_length (range2))
    {
      if (Range_length (range1) <= cache_size)
	{
	  memcpy (&cache[0], &array[range1.start],
		  Range_length (range1) * sizeof (array[0]));
	  memmove (&array[range1.start], &array[range2.start],
		   Range_length (range2) * sizeof (array[0]));
	  memcpy (&array[range1.start + Range_length (range2)], &cache[0],
		  Range_length (range1) * sizeof (array[0]));
	  return;
	}
    }
  else
    {
      if (Range_length (range2) <= cache_size)
	{
	  memcpy (&cache[0], &array[range2.start],
		  Range_length (range2) * sizeof (array[0]));
	  memmove (&array[range2.end - Range_length (range1)],
		   &array[range1.start],
		   Range_length (range1) * sizeof (array[0]));
	  memcpy (&array[range1.start], &cache[0],
		  Range_length (range2) * sizeof (array[0]));
	  return;
	}
    }

  Reverse (array, range1);
  Reverse (array, range2);
  Reverse (array, range);
}

/* standard merge operation using an internal or external buffer */
void
WikiMerge (Test array[], const Range buffer, const Range A, const Range B,
	   const Comparison compare, Test cache[], const long cache_size)
{
  /* if A fits into the cache, use that instead of the internal buffer */
  if (Range_length (A) <= cache_size)
    {
      Test *A_index = &cache[0];
      Test *B_index = &array[B.start];
      Test *insert_index = &array[A.start];
      Test *A_last = &cache[Range_length (A)];
      Test *B_last = &array[B.end];

      if (Range_length (B) > 0 && Range_length (A) > 0)
	{
	  while (true)
	    {
	      if (!compare (*B_index, *A_index))
		{
		  *insert_index = *A_index;
		  A_index++;
		  insert_index++;
		  if (A_index == A_last)
		    break;
		}
	      else
		{
		  *insert_index = *B_index;
		  B_index++;
		  insert_index++;
		  if (B_index == B_last)
		    break;
		}
	    }
	}

      /* copy the remainder of A into the final array */
      memcpy (insert_index, A_index, (A_last - A_index) * sizeof (array[0]));
    }
  else
    {
      /* whenever we find a value to add to the final array, swap it with the value that's already in that spot */
      /* when this algorithm is finished, 'buffer' will contain its original contents, but in a different order */
      long A_count = 0, B_count = 0, insert = 0;

      if (Range_length (B) > 0 && Range_length (A) > 0)
	{
	  while (true)
	    {
	      if (!compare
		  (array[B.start + B_count], array[buffer.start + A_count]))
		{
		  Swap (array[A.start + insert],
			array[buffer.start + A_count], Test);
		  A_count++;
		  insert++;
		  if (A_count >= Range_length (A))
		    break;
		}
	      else
		{
		  Swap (array[A.start + insert], array[B.start + B_count], Test);
		  B_count++;
		  insert++;
		  if (B_count >= Range_length (B))
		    break;
		}
	    }
	}

      /* swap the remainder of A into the final array */
      BlockSwap (array, buffer.start + A_count, A.start + insert,
		 Range_length (A) - A_count);
    }
}

/* bottom-up merge sort combined with an in-place merge algorithm for O(1) memory use */
void
WikiSort (Test array[], const long size, const Comparison compare)
{
  /* use a small cache to speed up some of the operations */
  /* since the cache size is fixed, it's still O(1) memory! */
  /* just keep in mind that making it too small ruins the point (nothing will fit into it), */
  /* and making it too large also ruins the point (so much for "low memory"!) */
  /* removing the cache entirely still gives 70% of the performance of a standard merge */

  /* also, if you change this to dynamically allocate a full-size buffer, */
  /* the algorithm seamlessly degenerates into a standard merge sort! */
#define CACHE_SIZE 512
  const long cache_size = CACHE_SIZE;
  Test cache[CACHE_SIZE];

  long index, merge_size, start, mid, end, fractional, decimal;
  long power_of_two, fractional_base, fractional_step, decimal_step;

  /* if there are 32 or fewer items, just insertion sort the entire array */
  if (size <= 32)
    {
      InsertionSort (array, MakeRange (0, size), compare);
      return;
    }

  /* calculate how to scale the index value to the range within the array */
  /* (this is essentially fixed-point math, where we manually check for and handle overflow) */
  power_of_two = FloorPowerOfTwo (size);
  fractional_base = power_of_two / 16;
  fractional_step = size % fractional_base;
  decimal_step = size / fractional_base;

  /* first insertion sort everything the lowest level, which is 16-31 items at a time */
  decimal = 0;
  fractional = 0;
  while (decimal < size)
    {
      start = decimal;

      decimal += decimal_step;
      fractional += fractional_step;
      if (fractional >= fractional_base)
	{
	  fractional -= fractional_base;
	  decimal += 1;
	}

      end = decimal;

      InsertionSort (array, MakeRange (start, end), compare);
    }

  /* then merge sort the higher levels, which can be 32-63, 64-127, 128-255, etc. */
  for (merge_size = 16; merge_size < power_of_two; merge_size += merge_size)
    {
      long block_size = sqrt (decimal_step);
      long buffer_size = decimal_step / block_size + 1;

      /* as an optimization, we really only need to pull out an internal buffer once for each level of merges */
      /* after that we can reuse the same buffer over and over, then redistribute it when we're finished with this level */
      Range level1 = MakeRange (0, 0);
      Range level2 = MakeRange (0, 0);
      Range levelA = MakeRange (0, 0);
      Range levelB = MakeRange (0, 0);

      decimal = fractional = 0;
      while (decimal < size)
	{
	  start = decimal;

	  decimal += decimal_step;
	  fractional += fractional_step;
	  if (fractional >= fractional_base)
	    {
	      fractional -= fractional_base;
	      decimal += 1;
	    }

	  mid = decimal;

	  decimal += decimal_step;
	  fractional += fractional_step;
	  if (fractional >= fractional_base)
	    {
	      fractional -= fractional_base;
	      decimal += 1;
	    }

	  end = decimal;

	  if (compare (array[end - 1], array[start]))
	    {
	      /* the two ranges are in reverse order, so a simple rotation should fix it */
	      Rotate (array, mid - start, MakeRange (start, end), cache,
		      cache_size);
	    }
	  else if (compare (array[mid], array[mid - 1]))
	    {
	      Range bufferA, bufferB, buffer1, buffer2, blockA, blockB,
		firstA, lastA, lastB;
	      long indexA, minA, findA;
	      Test min_value;

	      /* these two ranges weren't already in order, so we'll need to merge them! */
	      Range A = MakeRange (start, mid), B = MakeRange (mid, end);

	      /* try to fill up two buffers with unique values in ascending order */
	      if (Range_length (A) <= cache_size)
		{
		  memcpy (&cache[0], &array[A.start],
			  Range_length (A) * sizeof (array[0]));
		  WikiMerge (array, MakeRange (0, 0), A, B, compare, cache,
			     cache_size);
		  continue;
		}

	      if (Range_length (level1) > 0)
		{
		  /* reuse the buffers we found in a previous iteration */
		  bufferA = MakeRange (A.start, A.start);
		  bufferB = MakeRange (B.end, B.end);
		  buffer1 = level1;
		  buffer2 = level2;

		}
	      else
		{
		  long count, length;

		  /* the first item is always going to be the first unique value, so let's start searching at the next index */
		  count = 1;
		  for (buffer1.start = A.start + 1; buffer1.start < A.end;
		       buffer1.start++)
		    if (compare
			(array[buffer1.start - 1], array[buffer1.start])
			|| compare (array[buffer1.start],
				    array[buffer1.start - 1]))
		      if (++count == buffer_size)
			break;
		  buffer1.end = buffer1.start + count;

		  /* if the size of each block fits into the cache, we only need one buffer for tagging the A blocks */
		  /* this is because the other buffer is used as a swap space for merging the A blocks into the B values that follow it, */
		  /* but we can just use the cache as the buffer instead. this skips some memmoves and an insertion sort */
		  if (buffer_size <= cache_size)
		    {
		      buffer2 = MakeRange (A.start, A.start);

		      if (Range_length (buffer1) == buffer_size)
			{
			  /* we found enough values for the buffer in A */
			  bufferA =
			    MakeRange (buffer1.start,
				       buffer1.start + buffer_size);
			  bufferB = MakeRange (B.end, B.end);
			  buffer1 =
			    MakeRange (A.start, A.start + buffer_size);

			}
		      else
			{
			  /* we were unable to find enough unique values in A, so try B */
			  bufferA = MakeRange (buffer1.start, buffer1.start);
			  buffer1 = MakeRange (A.start, A.start);

			  /* the last value is guaranteed to be the first unique value we encounter, so we can start searching at the next index */
			  count = 1;
			  for (buffer1.start = B.end - 2;
			       buffer1.start >= B.start; buffer1.start--)
			    if (compare
				(array[buffer1.start],
				 array[buffer1.start + 1])
				|| compare (array[buffer1.start + 1],
					    array[buffer1.start]))
			      if (++count == buffer_size)
				break;
			  buffer1.end = buffer1.start + count;

			  if (Range_length (buffer1) == buffer_size)
			    {
			      bufferB =
				MakeRange (buffer1.start,
					   buffer1.start + buffer_size);
			      buffer1 =
				MakeRange (B.end - buffer_size, B.end);
			    }
			}
		    }
		  else
		    {
		      /* the first item of the second buffer isn't guaranteed to be the first unique value, so we need to find the first unique item too */
		      count = 0;
		      for (buffer2.start = buffer1.start + 1;
			   buffer2.start < A.end; buffer2.start++)
			if (compare
			    (array[buffer2.start - 1], array[buffer2.start])
			    || compare (array[buffer2.start],
					array[buffer2.start - 1]))
			  if (++count == buffer_size)
			    break;
		      buffer2.end = buffer2.start + count;

		      if (Range_length (buffer2) == buffer_size)
			{
			  /* we found enough values for both buffers in A */
			  bufferA =
			    MakeRange (buffer2.start,
				       buffer2.start + buffer_size * 2);
			  bufferB = MakeRange (B.end, B.end);
			  buffer1 =
			    MakeRange (A.start, A.start + buffer_size);
			  buffer2 =
			    MakeRange (A.start + buffer_size,
				       A.start + buffer_size * 2);

			}
		      else if (Range_length (buffer1) == buffer_size)
			{
			  /* we found enough values for one buffer in A, so we'll need to find one buffer in B */
			  bufferA =
			    MakeRange (buffer1.start,
				       buffer1.start + buffer_size);
			  buffer1 =
			    MakeRange (A.start, A.start + buffer_size);

			  /* like before, the last value is guaranteed to be the first unique value we encounter, so we can start searching at the next index */
			  count = 1;
			  for (buffer2.start = B.end - 2;
			       buffer2.start >= B.start; buffer2.start--)
			    if (compare
				(array[buffer2.start],
				 array[buffer2.start + 1])
				|| compare (array[buffer2.start + 1],
					    array[buffer2.start]))
			      if (++count == buffer_size)
				break;
			  buffer2.end = buffer2.start + count;

			  if (Range_length (buffer2) == buffer_size)
			    {
			      bufferB =
				MakeRange (buffer2.start,
					   buffer2.start + buffer_size);
			      buffer2 =
				MakeRange (B.end - buffer_size, B.end);

			    }
			  else
			    buffer1.end = buffer1.start;	/* failure */
			}
		      else
			{
			  /* we were unable to find a single buffer in A, so we'll need to find two buffers in B */
			  count = 1;
			  for (buffer1.start = B.end - 2;
			       buffer1.start >= B.start; buffer1.start--)
			    if (compare
				(array[buffer1.start],
				 array[buffer1.start + 1])
				|| compare (array[buffer1.start + 1],
					    array[buffer1.start]))
			      if (++count == buffer_size)
				break;
			  buffer1.end = buffer1.start + count;

			  count = 0;
			  for (buffer2.start = buffer1.start - 1;
			       buffer2.start >= B.start; buffer2.start--)
			    if (compare
				(array[buffer2.start],
				 array[buffer2.start + 1])
				|| compare (array[buffer2.start + 1],
					    array[buffer2.start]))
			      if (++count == buffer_size)
				break;
			  buffer2.end = buffer2.start + count;

			  if (Range_length (buffer2) == buffer_size)
			    {
			      bufferA = MakeRange (A.start, A.start);
			      bufferB =
				MakeRange (buffer2.start,
					   buffer2.start + buffer_size * 2);
			      buffer1 =
				MakeRange (B.end - buffer_size, B.end);
			      buffer2 =
				MakeRange (buffer1.start - buffer_size,
					   buffer1.start);

			    }
			  else
			    buffer1.end = buffer1.start;	/* failure */
			}
		    }

		  if (Range_length (buffer1) < buffer_size)
		    {
		      /* we failed to fill both buffers with unique values, which implies we're merging two subarrays with a lot of the same values repeated */
		      /* we can use this knowledge to write a merge operation that is optimized for arrays of repeating values */
		      while (Range_length (A) > 0 && Range_length (B) > 0)
			{
			  /* find the first place in B where the first item in A needs to be inserted */
			  long local_mid = BinaryFirst (array, A.start, B, compare);

			  /* rotate A into place */
			  long amount = local_mid - A.end;
			  Rotate (array, -amount, MakeRange (A.start, local_mid),
				  cache, cache_size);

			  /* calculate the new A and B ranges */
			  B.start = local_mid;
			  A =
			    MakeRange (BinaryLast
				       (array, A.start + amount, A, compare),
				       B.start);
			}

		      continue;
		    }

		  /* move the unique values to the start of A if needed */
		  length = Range_length (bufferA);
		  count = 0;
		  for (index = bufferA.start; count < length; index--)
		    {
		      if (index == A.start
			  || compare (array[index - 1], array[index])
			  || compare (array[index], array[index - 1]))
			{
			  Rotate (array, -count,
				  MakeRange (index + 1, bufferA.start + 1),
				  cache, cache_size);
			  bufferA.start = index + count;
			  count++;
			}
		    }
		  bufferA = MakeRange (A.start, A.start + length);

		  /* move the unique values to the end of B if needed */
		  length = Range_length (bufferB);
		  count = 0;
		  for (index = bufferB.start; count < length; index++)
		    {
		      if (index == B.end - 1
			  || compare (array[index], array[index + 1])
			  || compare (array[index + 1], array[index]))
			{
			  Rotate (array, count,
				  MakeRange (bufferB.start, index), cache,
				  cache_size);
			  bufferB.start = index - count;
			  count++;
			}
		    }
		  bufferB = MakeRange (B.end - length, B.end);

		  /* reuse these buffers next time! */
		  level1 = buffer1;
		  level2 = buffer2;
		  levelA = bufferA;
		  levelB = bufferB;
		}

	      /* break the remainder of A into blocks. firstA is the uneven-sized first A block */
	      blockA = MakeRange (bufferA.end, A.end);
	      firstA =
		MakeRange (bufferA.end,
			   bufferA.end + Range_length (blockA) % block_size);

	      /* swap the second value of each A block with the value in buffer1 */
	      index = 0;
	      for (indexA = firstA.end + 1; indexA < blockA.end;
		   index++, indexA += block_size)
		Swap (array[buffer1.start + index], array[indexA], Test);

	      /* start rolling the A blocks through the B blocks! */
	      /* whenever we leave an A block behind, we'll need to merge the previous A block with any B blocks that follow it, so track that information as well */
	      lastA = firstA;
	      lastB = MakeRange (0, 0);
	      blockB =
		MakeRange (B.start,
			   B.start + Min (block_size,
					  Range_length (B) -
					  Range_length (bufferB)));
	      blockA.start += Range_length (firstA);

	      minA = blockA.start;
	      min_value = array[minA];
	      indexA = 0;

	      if (Range_length (lastA) <= cache_size)
		memcpy (&cache[0], &array[lastA.start],
			Range_length (lastA) * sizeof (array[0]));
	      else
		BlockSwap (array, lastA.start, buffer2.start,
			   Range_length (lastA));

	      while (true)
		{
		  /* if there's a previous B block and the first value of the minimum A block is <= the last value of the previous B block */
		  if ((Range_length (lastB) > 0
		       && !compare (array[lastB.end - 1], min_value))
		      || Range_length (blockB) == 0)
		    {
		      /* figure out where to split the previous B block, and rotate it at the split */
		      long B_split =
			BinaryFirst (array, minA, lastB, compare);
		      long B_remaining = lastB.end - B_split;

		      /* swap the minimum A block to the beginning of the rolling A blocks */
		      BlockSwap (array, blockA.start, minA, block_size);

		      /* we need to swap the second item of the previous A block back with its original value, which is stored in buffer1 */
		      /* since the firstA block did not have its value swapped out, we need to make sure the previous A block is not unevenly sized */
		      Swap (array[blockA.start + 1],
			    array[buffer1.start + indexA++], Test);

		      /* locally merge the previous A block with the B values that follow it, using the buffer as swap space */
		      WikiMerge (array, buffer2, lastA,
				 MakeRange (lastA.end, B_split), compare,
				 cache, cache_size);

		      /* copy the previous A block into the cache or buffer2, since that's where we need it to be when we go to merge it anyway */
		      if (block_size <= cache_size)
			memcpy (&cache[0], &array[blockA.start],
				block_size * sizeof (array[0]));
		      else
			BlockSwap (array, blockA.start, buffer2.start,
				   block_size);

		      /* this is equivalent to rotating, but faster */
		      /* the area normally taken up by the A block is either the contents of buffer2, or data we don't need anymore since we memcopied it */
		      /* either way, we don't need to retain the order of those items, so instead of rotating we can just block swap B to where it belongs */
		      BlockSwap (array, B_split,
				 blockA.start + block_size - B_remaining,
				 B_remaining);

		      /* now we need to update the ranges and stuff */
		      lastA =
			MakeRange (blockA.start - B_remaining,
				   blockA.start - B_remaining + block_size);
		      lastB = MakeRange (lastA.end, lastA.end + B_remaining);
		      blockA.start += block_size;
		      if (Range_length (blockA) == 0)
			break;

		      /* search the second value of the remaining A blocks to find the new minimum A block (that's why we wrote unique values to them!) */
		      minA = blockA.start + 1;
		      for (findA = minA + block_size; findA < blockA.end;
			   findA += block_size)
			if (compare (array[findA], array[minA]))
			  minA = findA;
		      minA = minA - 1;	/* decrement once to get back to the start of that A block */
		      min_value = array[minA];

		    }
		  else if (Range_length (blockB) < block_size)
		    {
		      /* move the last B block, which is unevenly sized, to before the remaining A blocks, by using a rotation */
		      /* (using the cache is disabled since we have the contents of the previous A block in it!) */
		      Rotate (array, -Range_length (blockB),
			      MakeRange (blockA.start, blockB.end), cache, 0);
		      lastB =
			MakeRange (blockA.start,
				   blockA.start + Range_length (blockB));
		      blockA.start += Range_length (blockB);
		      blockA.end += Range_length (blockB);
		      minA += Range_length (blockB);
		      blockB.end = blockB.start;

		    }
		  else
		    {
		      /* roll the leftmost A block to the end by swapping it with the next B block */
		      BlockSwap (array, blockA.start, blockB.start,
				 block_size);
		      lastB =
			MakeRange (blockA.start, blockA.start + block_size);
		      if (minA == blockA.start)
			minA = blockA.end;

		      blockA.start += block_size;
		      blockA.end += block_size;
		      blockB.start += block_size;
		      blockB.end += block_size;
		      if (blockB.end > bufferB.start)
			blockB.end = bufferB.start;
		    }
		}

	      /* merge the last A block with the remaining B blocks */
	      WikiMerge (array, buffer2, lastA,
			 MakeRange (lastA.end,
				    B.end - Range_length (bufferB)), compare,
			 cache, cache_size);
	    }
	}

      if (Range_length (level1) > 0)
	{
	  long level_start;

	  /* when we're finished with this step we should have b1 b2 left over, where one of the buffers is all jumbled up */
	  /* insertion sort the jumbled up buffer, then redistribute them back into the array using the opposite process used for creating the buffer */
	  InsertionSort (array, level2, compare);

	  /* redistribute bufferA back into the array */
	  level_start = levelA.start;
	  for (index = levelA.end; Range_length (levelA) > 0; index++)
	    {
	      if (index == levelB.start
		  || !compare (array[index], array[levelA.start]))
		{
		  long amount = index - levelA.end;
		  Rotate (array, -amount, MakeRange (levelA.start, index),
			  cache, cache_size);
		  levelA.start += (amount + 1);
		  levelA.end += amount;
		  index--;
		}
	    }

	  /* redistribute bufferB back into the array */
	  for (index = levelB.start; Range_length (levelB) > 0; index--)
	    {
	      if (index == level_start
		  || !compare (array[levelB.end - 1], array[index - 1]))
		{
		  long amount = levelB.start - index;
		  Rotate (array, amount, MakeRange (index, levelB.end), cache,
			  cache_size);
		  levelB.start -= amount;
		  levelB.end -= (amount + 1);
		  index++;
		}
	    }
	}

      decimal_step += decimal_step;
      fractional_step += fractional_step;
      if (fractional_step >= fractional_base)
	{
	  fractional_step -= fractional_base;
	  decimal_step += 1;
	}
    }

#undef CACHE_SIZE
}



long
TestingPathological (long index, long total)
{
  if (index == 0)
    return 10;
  else if (index < total / 2)
    return 11;
  else if (index == total - 1)
    return 10;
  return 9;
}

long
TestingRandom (long index, long total)
{
  return rand_beebs ();
}

long
TestingMostlyDescending (long index, long total)
{
  return total - index + rand_beebs () * 1.0 / RAND_MAX * 5 - 2.5;
}

long
TestingMostlyAscending (long index, long total)
{
  return index + rand_beebs () * 1.0 / RAND_MAX * 5 - 2.5;
}

long
TestingAscending (long index, long total)
{
  return index;
}

long
TestingDescending (long index, long total)
{
  return total - index;
}

long
TestingEqual (long index, long total)
{
  return 1000;
}

long
TestingJittered (long index, long total)
{
  return (rand_beebs () * 1.0 / RAND_MAX <= 0.9) ? index : (index - 2);
}

long
TestingMostlyEqual (long index, long total)
{
  return 1000L + (long) (rand_beebs () % 4);
}


const long max_size = 400;
Test array1[400];


/* This benchmark does not support verification */

int
verify_benchmark_wikisort (int res __attribute ((unused)))
{
  Test exp[] = {
    {1000, 1}, {1000, 2}, {1000, 13}, {1000, 18}, {1000, 19},
    {1000, 26}, {1000, 31}, {1000, 32}, {1000, 35}, {1000, 36},
    {1000, 37}, {1000, 46}, {1000, 49}, {1000, 55}, {1000, 61},
    {1000, 62}, {1000, 66}, {1000, 72}, {1000, 73}, {1000, 74},
    {1000, 75}, {1000, 76}, {1000, 77}, {1000, 81}, {1000, 82},
    {1000, 83}, {1000, 87}, {1000, 89}, {1000, 91}, {1000, 92},
    {1000, 95}, {1000, 99}, {1000, 101}, {1000, 105}, {1000, 108},
    {1000, 109}, {1000, 114}, {1000, 119}, {1000, 120}, {1000, 128},
    {1000, 137}, {1000, 143}, {1000, 144}, {1000, 151}, {1000, 158},
    {1000, 161}, {1000, 162}, {1000, 165}, {1000, 169}, {1000, 181},
    {1000, 182}, {1000, 187}, {1000, 188}, {1000, 190}, {1000, 195},
    {1000, 196}, {1000, 198}, {1000, 200}, {1000, 201}, {1000, 205},
    {1000, 206}, {1000, 211}, {1000, 212}, {1000, 213}, {1000, 214},
    {1000, 215}, {1000, 217}, {1000, 221}, {1000, 223}, {1000, 225},
    {1000, 226}, {1000, 227}, {1000, 233}, {1000, 242}, {1000, 245},
    {1000, 249}, {1000, 250}, {1000, 266}, {1000, 270}, {1000, 271},
    {1000, 273}, {1000, 274}, {1000, 280}, {1000, 287}, {1000, 291},
    {1000, 295}, {1000, 299}, {1000, 303}, {1000, 304}, {1000, 312},
    {1000, 328}, {1000, 330}, {1000, 333}, {1000, 339}, {1000, 342},
    {1000, 346}, {1000, 350}, {1000, 361}, {1000, 371}, {1000, 376},
    {1000, 378}, {1000, 382}, {1000, 384}, {1000, 385}, {1000, 390},
    {1000, 396}, {1001, 5}, {1001, 7}, {1001, 8}, {1001, 11},
    {1001, 16}, {1001, 20}, {1001, 21}, {1001, 22}, {1001, 29},
    {1001, 34}, {1001, 39}, {1001, 40}, {1001, 41}, {1001, 42},
    {1001, 47}, {1001, 54}, {1001, 63}, {1001, 68}, {1001, 71},
    {1001, 78}, {1001, 84}, {1001, 85}, {1001, 93}, {1001, 96},
    {1001, 97}, {1001, 103}, {1001, 104}, {1001, 107}, {1001, 117},
    {1001, 129}, {1001, 139}, {1001, 140}, {1001, 148}, {1001, 156},
    {1001, 160}, {1001, 167}, {1001, 172}, {1001, 174}, {1001, 175},
    {1001, 179}, {1001, 185}, {1001, 186}, {1001, 193}, {1001, 194},
    {1001, 207}, {1001, 208}, {1001, 216}, {1001, 219}, {1001, 224},
    {1001, 228}, {1001, 229}, {1001, 235}, {1001, 237}, {1001, 240},
    {1001, 246}, {1001, 252}, {1001, 255}, {1001, 256}, {1001, 257},
    {1001, 259}, {1001, 260}, {1001, 261}, {1001, 265}, {1001, 267},
    {1001, 269}, {1001, 275}, {1001, 286}, {1001, 288}, {1001, 289},
    {1001, 294}, {1001, 301}, {1001, 302}, {1001, 308}, {1001, 309},
    {1001, 314}, {1001, 322}, {1001, 323}, {1001, 325}, {1001, 326},
    {1001, 327}, {1001, 334}, {1001, 337}, {1001, 341}, {1001, 347},
    {1001, 352}, {1001, 357}, {1001, 360}, {1001, 363}, {1001, 365},
    {1001, 366}, {1001, 369}, {1001, 375}, {1001, 379}, {1001, 381},
    {1001, 393}, {1001, 394}, {1001, 398}, {1002, 9}, {1002, 17},
    {1002, 23}, {1002, 24}, {1002, 30}, {1002, 33}, {1002, 38},
    {1002, 43}, {1002, 45}, {1002, 53}, {1002, 57}, {1002, 59},
    {1002, 60}, {1002, 64}, {1002, 69}, {1002, 70}, {1002, 79},
    {1002, 88}, {1002, 94}, {1002, 98}, {1002, 100}, {1002, 110},
    {1002, 111}, {1002, 115}, {1002, 118}, {1002, 123}, {1002, 125},
    {1002, 127}, {1002, 130}, {1002, 131}, {1002, 134}, {1002, 136},
    {1002, 138}, {1002, 142}, {1002, 146}, {1002, 149}, {1002, 150},
    {1002, 152}, {1002, 153}, {1002, 157}, {1002, 163}, {1002, 166},
    {1002, 168}, {1002, 170}, {1002, 171}, {1002, 173}, {1002, 176},
    {1002, 177}, {1002, 180}, {1002, 183}, {1002, 184}, {1002, 189},
    {1002, 191}, {1002, 197}, {1002, 202}, {1002, 203}, {1002, 204},
    {1002, 210}, {1002, 218}, {1002, 220}, {1002, 232}, {1002, 236},
    {1002, 238}, {1002, 241}, {1002, 243}, {1002, 244}, {1002, 251},
    {1002, 253}, {1002, 254}, {1002, 258}, {1002, 264}, {1002, 272},
    {1002, 277}, {1002, 279}, {1002, 282}, {1002, 283}, {1002, 284},
    {1002, 290}, {1002, 292}, {1002, 296}, {1002, 297}, {1002, 298},
    {1002, 300}, {1002, 306}, {1002, 307}, {1002, 310}, {1002, 311},
    {1002, 315}, {1002, 316}, {1002, 319}, {1002, 321}, {1002, 324},
    {1002, 331}, {1002, 335}, {1002, 340}, {1002, 344}, {1002, 349},
    {1002, 353}, {1002, 354}, {1002, 358}, {1002, 362}, {1002, 364},
    {1002, 370}, {1002, 374}, {1002, 380}, {1002, 383}, {1002, 386},
    {1002, 389}, {1002, 391}, {1002, 392}, {1002, 397}, {1003, 0},
    {1003, 3}, {1003, 4}, {1003, 6}, {1003, 10}, {1003, 12},
    {1003, 14}, {1003, 15}, {1003, 25}, {1003, 27}, {1003, 28},
    {1003, 44}, {1003, 48}, {1003, 50}, {1003, 51}, {1003, 52},
    {1003, 56}, {1003, 58}, {1003, 65}, {1003, 67}, {1003, 80},
    {1003, 86}, {1003, 90}, {1003, 102}, {1003, 106}, {1003, 112},
    {1003, 113}, {1003, 116}, {1003, 121}, {1003, 122}, {1003, 124},
    {1003, 126}, {1003, 132}, {1003, 133}, {1003, 135}, {1003, 141},
    {1003, 145}, {1003, 147}, {1003, 154}, {1003, 155}, {1003, 159},
    {1003, 164}, {1003, 178}, {1003, 192}, {1003, 199}, {1003, 209},
    {1003, 222}, {1003, 230}, {1003, 231}, {1003, 234}, {1003, 239},
    {1003, 247}, {1003, 248}, {1003, 262}, {1003, 263}, {1003, 268},
    {1003, 276}, {1003, 278}, {1003, 281}, {1003, 285}, {1003, 293},
    {1003, 305}, {1003, 313}, {1003, 317}, {1003, 318}, {1003, 320},
    {1003, 329}, {1003, 332}, {1003, 336}, {1003, 338}, {1003, 343},
    {1003, 345}, {1003, 348}, {1003, 351}, {1003, 355}, {1003, 356},
    {1003, 359}, {1003, 367}, {1003, 368}, {1003, 372}, {1003, 373},
    {1003, 377}, {1003, 387}, {1003, 388}, {1003, 395}, {1003, 399}
  };

  return 0 == memcmp (array1, exp, max_size * sizeof (array1[0]));
}


void
initialise_benchmark_wikisort (void)
{
}


static int benchmark_body_wikisort (int  rpt);

void
warm_caches_wikisort (int  heat)
{
  benchmark_body_wikisort (heat);

  return;
}


int
benchmark_wikisort (void)
{
  return benchmark_body_wikisort (LOCAL_SCALE_FACTOR * CPU_MHZ);
}


static int __attribute__ ((noinline))
benchmark_body_wikisort (int rpt)
{
  long total, index, test_case;
  Comparison compare = TestCompare;

  TestCasePtr test_cases[9] =
  {
  &TestingPathological,
      &TestingRandom,
      &TestingMostlyDescending,
      &TestingMostlyAscending,
      &TestingAscending,
      &TestingDescending,
      &TestingEqual, &TestingJittered, &TestingMostlyEqual};

  int i;

  for (i = 0; i < rpt; i++)
    {
      /* initialize the random-number generator. */
      /* The original code used srand here, we use a value that will fit in
         a 16-bit unsigned int. */
      srand_beebs (0);
      /*srand(10141985); *//* in case you want the same random numbers */

      total = max_size;
      for (test_case = 0; test_case < 9; test_case++)
	{

	  for (index = 0; index < total; index++)
	    {
	      Test item;

	      item.value = test_cases[test_case] (index, total);
	      item.index = index;

	      array1[index] = item;
	    }

	  WikiSort (array1, total, compare);
	}
    }

  return 0;
}


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
