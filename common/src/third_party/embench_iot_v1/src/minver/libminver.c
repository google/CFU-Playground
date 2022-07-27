/* BEEBS minver benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor Pierre Langlois <pierre.langlois@embecosm.com>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later

   *************************************************************************
   *                                                                       *
   *   SNU-RT Benchmark Suite for Worst Case Timing Analysis               *
   *   =====================================================               *
   *                              Collected and Modified by S.-S. Lim      *
   *                                           sslim@archi.snu.ac.kr       *
   *                                         Real-Time Research Group      *
   *                                        Seoul National University      *
   *                                                                       *
   *                                                                       *
   *        < Features > - restrictions for our experimental environment   *
   *                                                                       *
   *          1. Completely structured.                                    *
   *               - There are no unconditional jumps.                     *
   *               - There are no exit from loop bodies.                   *
   *                 (There are no 'break' or 'return' in loop bodies)     *
   *          2. No 'switch' statements.                                   *
   *          3. No 'do..while' statements.                                *
   *          4. Expressions are restricted.                               *
   *               - There are no multiple expressions joined by 'or',     *
   *                'and' operations.                                      *
   *          5. No library calls.                                         *
   *               - All the functions needed are implemented in the       *
   *                 source file.                                          *
   *                                                                       *
   *                                                                       *
   *************************************************************************
   *                                                                       *
   *  FILE: minver.c                                                       *
   *  SOURCE : Turbo C Programming for Engineering by Hyun Soo Ahn         *
   *                                                                       *
   *  DESCRIPTION :                                                        *
   *                                                                       *
   *     Matrix inversion for 3x3 floating point matrix.                   *
   *                                                                       *
   *  REMARK :                                                             *
   *                                                                       *
   *  EXECUTION TIME :                                                     *
   *                                                                       *
   *                                                                       *
   *************************************************************************

*/

#include <math.h>
#include <string.h>
#include "third_party/embench_iot_v1/support/support.h"

/* This scale factor will be changed to equalise the runtime of the
   benchmarks. */
#define LOCAL_SCALE_FACTOR 555

int minver (int row, int col, float eps);
int mmul (int row_a, int col_a, int row_b, int col_b);

static float a_ref[3][3] = {
  {3.0f, -6.0f, 7.0f},
  {9.0f, 0.0f, -5.0f},
  {5.0f, -8.0f, 6.0f},
};

static float b[3][3] = {
  {-3.0f, 0.0f, 2.0f},
  {3.0f, -2.0f, 0.0f},
  {0.0f, 2.0f, -3.0f},
};

static float a[3][3], c[3][3], d[3][3], det;

static float
minver_fabs (float n)
{
  float f;

  if (n >= 0)
    f = n;
  else
    f = -n;
  return f;
}

int
mmul (int row_a, int col_a, int row_b, int col_b)
{
  int i, j, k, row_c, col_c;
  float w;

  row_c = row_a;
  col_c = col_b;

  if (row_c < 1 || row_b < 1 || col_c < 1 || col_a != row_b)
    return (999);
  for (i = 0; i < row_c; i++)
    {
      for (j = 0; j < col_c; j++)
	{
	  w = 0.0f;
	  for (k = 0; k < row_b; k++)
	    w += a[i][k] * b[k][j];
	  c[i][j] = w;
	}
    }

  return (0);
}


int
minver (int row, int col, float eps)
{
  int work[500], i, j, k, r, iw, u, v;
  float w, wmax, pivot, api, w1;

  r = w = 0;
  if (row < 2 || row > 500 || eps <= 0.0f)
    return (999);
  w1 = 1.0f;
  for (i = 0; i < row; i++)
    work[i] = i;
  for (k = 0; k < row; k++)
    {
      wmax = 0.0f;
      for (i = k; i < row; i++)
	{
	  w = minver_fabs (a[i][k]);
	  if (w > wmax)
	    {
	      wmax = w;
	      r = i;
	    }
	}
      pivot = a[r][k];
      api = minver_fabs (pivot);
      if (api <= eps)
	{
	  det = w1;
	  return (1);
	}
      w1 *= pivot;
      u = k * col;
      v = r * col;
      if (r != k)
	{
	  w1 = -w;
	  iw = work[k];
	  work[k] = work[r];
	  work[r] = iw;
	  for (j = 0; j < row; j++)
	    {
	      w = a[k][j];
	      a[k][j] = a[r][j];
	      a[r][j] = w;
	    }
	}
      for (i = 0; i < row; i++)
	a[k][i] /= pivot;
      for (i = 0; i < row; i++)
	{
	  if (i != k)
	    {
	      v = i * col;
	      w = a[i][k];
	      if (w != 0.0f)
		{
		  for (j = 0; j < row; j++)
		    if (j != k)
		      a[i][j] -= w * a[k][j];
		  a[i][k] = -w / pivot;
		}
	    }
	}
      a[k][k] = 1.0f / pivot;
    }

  for (i = 0; i < row; i++)
    {
      while (1)
	{
	  k = work[i];
	  if (k == i)
	    break;
	  iw = work[k];
	  work[k] = work[i];
	  work[i] = iw;
	  for (j = 0; j < row; j++)
	    {
	      u = j * col;
	      w = a[k][i];
	      a[k][i] = a[k][k];
	      a[k][k] = w;
	    }
	}
    }

  det = w1;

  return (0);
}


int
verify_benchmark_minver (int res __attribute ((unused)))
{
  int i, j;
  /* float eps = 1.0e-6; UNUSED VARIABLE */

  static float c_exp[3][3] = {
    {-27.0f, 26.0f, -15.0f},
    {-27.0f, -10.0f, 33.0f},
    {-39.0f, 28.0f, -8.0f}
  };

  static float d_exp[3][3] = {
    {0.133333325f, -0.199999958f, 0.2666665910f},
    {-0.519999862f, 0.113333330f, 0.5266665220f},
    {0.479999840f, -0.359999895f, 0.0399999917f}
  };

  /* Allow small errors in floating point */

  for (i = 0; i < 3; i++)
    for (j = 0; j < 3; j++)
      if (float_neq_beebs(c[i][j], c_exp[i][j]) || float_neq_beebs(d[i][j], d_exp[i][j]))
	return 0;

  return float_eq_beebs(det, -16.6666718f);
}


void
initialise_benchmark_minver (void)
{
}


static int benchmark_body_minver (int  rpt);

void
warm_caches_minver (int  heat)
{
  benchmark_body_minver (heat);

  return;
}


int
benchmark_minver (void)
{
  return benchmark_body_minver (LOCAL_SCALE_FACTOR * CPU_MHZ);
}


static int __attribute__ ((noinline))
benchmark_body_minver (int rpt)
{
  int i;

  for (i = 0; i < rpt; i++)
    {
      float eps = 1.0e-6f;

      memcpy (a, a_ref, 3 * 3 * sizeof (a[0][0]));
      minver (3, 3, eps);
      memcpy (d, a, 3 * 3 * sizeof (a[0][0]));
      memcpy (a, a_ref, 3 * 3 * sizeof (a[0][0]));
      mmul (3, 3, 3, 3);
    }

  return 0;
}


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
